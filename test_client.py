import asyncio
import websockets
import json

async def test_chat():
    uri = "ws://localhost:8000/ws/chat"
    async with websockets.connect(uri) as websocket:
        print("Connected!")
        
        # Send first message
        await websocket.send(json.dumps({"text": "I need a refund for ORD-2016. My Customer ID is C015."}))
        
        while True:
            try:
                response = await websocket.recv()
                data = json.loads(response)
                print(f"Received: {data['type']} | Content: {data.get('content', '')}".encode('ascii', 'ignore').decode('ascii'))
                if data['type'] == 'end':
                    break
            except Exception as e:
                print(f"Error: {e}")
                break

if __name__ == "__main__":
    asyncio.run(test_chat())
