import os
import operator
from typing import Annotated, Sequence, TypedDict, Literal
from pathlib import Path

from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from pydantic import BaseModel
from dotenv import load_dotenv

# Explicitly load the .env file from the backend root
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BASE_DIR / ".env")

from app.prompts import TRIAGE_AGENT_PROMPT, POLICY_AGENT_PROMPT, ACTION_AGENT_PROMPT, supervisor_prompt
from app.tools import get_customer_info, get_order_details, process_refund, deny_refund, check_policy

# State definition
class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    next: str

# Initialize LLM
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)

# Create distinct LLMs for routing vs generating so we can filter streams
worker_llm = llm.with_config({"tags": ["worker"]})
supervisor_llm = llm.with_config({"tags": ["supervisor"]})

# 1. Create Workers
triage_agent = create_react_agent(
    worker_llm, 
    tools=[get_customer_info, check_policy], 
    prompt=TRIAGE_AGENT_PROMPT
)

policy_agent = create_react_agent(
    worker_llm, 
    tools=[get_order_details, check_policy], 
    prompt=POLICY_AGENT_PROMPT
)

action_agent = create_react_agent(
    worker_llm, 
    tools=[process_refund, deny_refund], 
    prompt=ACTION_AGENT_PROMPT
)

# Wrapper nodes for workers to format output back to the main graph state
def sanitize_output(new_messages, agent_name):
    if not new_messages: return new_messages
    msg = new_messages[-1]
    content = getattr(msg, "content", "")
    if isinstance(content, list):
        content = "".join([b.get("text", "") for b in content if isinstance(b, dict) and "text" in b])
    
    # Cast inter-agent communication to HumanMessage so the next agent is forced to respond
    sanitized_msg = HumanMessage(content=content, name=agent_name)
    return [sanitized_msg]

def triage_node(state: AgentState):
    result = triage_agent.invoke({"messages": state["messages"]})
    new_messages = result["messages"][len(state["messages"]):]
    return {"messages": sanitize_output(new_messages, "Triage")}

def policy_node(state: AgentState):
    result = policy_agent.invoke({"messages": state["messages"]})
    new_messages = result["messages"][len(state["messages"]):]
    return {"messages": sanitize_output(new_messages, "Policy")}

def action_node(state: AgentState):
    result = action_agent.invoke({"messages": state["messages"]})
    new_messages = result["messages"][len(state["messages"]):]
    if new_messages:
        new_messages[-1].name = "Action"
    return {"messages": new_messages}

# 3. Build Graph
workflow = StateGraph(AgentState)

workflow.add_node("Triage", triage_node)
workflow.add_node("Policy", policy_node)
workflow.add_node("Action", action_node)

workflow.add_edge(START, "Triage")

# Add edges from workers back to Supervisor or to the next deterministic step
def is_internal(state):
    if not state.get("messages"): return False
    msg = state["messages"][-1]
    content = getattr(msg, "content", "")
    if isinstance(content, list):
        content = "".join([b.get("text", "") for b in content if isinstance(b, dict) and "text" in b])
    return "[INTERNAL]" in content

workflow.add_conditional_edges(
    "Triage",
    lambda state: "Policy" if is_internal(state) else END
)
workflow.add_edge("Policy", "Action")
workflow.add_edge("Action", END)

# Compile
memory = MemorySaver()
app_graph = workflow.compile(checkpointer=memory)
