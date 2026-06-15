import asyncio
import websockets
import json

async def simulate_backend(websocket, path):
    print("Client connected")
    try:
        async for message in websocket:
            print(f"Received: {message}")
            
            # Send stream
            await websocket.send(json.dumps({"type": "stream", "content": "This "}))
            await asyncio.sleep(0.5)
            await websocket.send(json.dumps({"type": "stream", "content": "is a "}))
            await asyncio.sleep(0.5)
            await websocket.send(json.dumps({"type": "stream", "content": "test."}))
            
            # Send end
            await websocket.send(json.dumps({"type": "end"}))
    except websockets.exceptions.ConnectionClosed:
        print("Client disconnected")

async def main():
    server = await websockets.serve(simulate_backend, "localhost", 8001)
    print("Test WebSocket server running on ws://localhost:8001")
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())
