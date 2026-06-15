import asyncio
from app.agent import app_graph
from langchain_core.messages import HumanMessage

async def main():
    config = {"configurable": {"thread_id": "test_123"}}
    state = {"messages": [HumanMessage(content="I need a refund for ORD-2016. My Customer ID is C015.")]}
    
    final_state = await app_graph.ainvoke(state, config=config)
    
    for i, msg in enumerate(final_state["messages"]):
        print(f"\n--- Message {i} ({msg.type} - {getattr(msg, 'name', 'None')}) ---")
        print(msg.content)
        if hasattr(msg, 'tool_calls'):
            print("Tool calls:", msg.tool_calls)

if __name__ == "__main__":
    asyncio.run(main())
