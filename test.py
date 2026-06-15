import asyncio
import sys
import json
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent / "backend"))

from backend.app.agent import app_graph
from langchain_core.messages import HumanMessage

async def main():
    config = {"configurable": {"thread_id": "test_15"}}
    inputs = {"messages": [HumanMessage(content="I wanted to retrun ORD-1015, it was cnfomd wotj a email address")]}
    
    current_node = ""
    try:
        async for event in app_graph.astream_events(inputs, config=config, version="v2"):
            kind = event["event"]
            name = event.get("name", "")
            
            if kind == "on_chain_start" and name in ["triage_node", "policy_node", "action_node", "supervisor_node", "Triage", "Policy", "Action", "Supervisor"]:
                current_node = name
                print(f"\n--- NODE ACTIVE: {name} ---")
            elif kind == "on_tool_start":
                print(f"Executing tool: {name}")
                if "input" in event["data"]:
                    print(f"Tool input: {event['data']['input']}")
            elif kind == "on_chain_end" and name in ["Triage", "Policy", "Action", "Supervisor"]:
                output = event["data"].get("output", {})
                if isinstance(output, dict) and "messages" in output:
                    msg = output["messages"][-1]
                    print(f"[{name} Output]: {msg.content}")
                elif isinstance(output, dict) and "next" in output:
                    print(f"[{name} Output (Route)]: {output['next']}")
    except Exception as e:
        print(f"CRASH: {e}")

if __name__ == "__main__":
    asyncio.run(main())
