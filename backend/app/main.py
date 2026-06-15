from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
import json
import os
from elevenlabs.client import ElevenLabs

from app.agent import app_graph

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

elevenlabs_client = ElevenLabs(api_key=os.environ.get("ELEVENLABS_API_KEY"))

class TTSRequest(BaseModel):
    text: str

@app.get("/api/tts")
async def generate_tts(text: str):
    # Strip asterisks for cleaner speech
    clean_text = text.replace("*", "")
    
    # Generate audio stream from elevenlabs
    audio_stream = elevenlabs_client.text_to_speech.convert(
        text=clean_text,
        voice_id="JBFqnCBsd6RMkjVDRZzb", # George (conversational)
        model_id="eleven_turbo_v2_5", # Turbo model for fast latency
        output_format="mp3_44100_128"
    )
    return StreamingResponse(audio_stream, media_type="audio/mpeg")

@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    thread_id = str(id(websocket))
    config = {"configurable": {"thread_id": thread_id}}
    
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            user_input = msg.get("text", "")
            
            if not user_input:
                continue

            # Stream LangGraph events using v2
            current_node = ""
            current_message_buffer = ""
            mute_stream = False
            async for event in app_graph.astream_events({"messages": [HumanMessage(content=user_input)]}, config=config, version="v2"):
                kind = event["event"]
                name = event.get("name", "")
                
                if kind == "on_chain_start" and name in ["triage_node", "policy_node", "action_node", "supervisor_node", "Triage", "Policy", "Action", "Supervisor"]:
                    current_node = name
                    print(f"Node Active: {name}", flush=True)
                    await websocket.send_text(json.dumps({"type": "log", "content": f"🔄 Node Active: {name}"}))
                
                elif kind == "on_chat_model_stream":
                    if current_node in ["Supervisor", "supervisor_node", "Policy", "policy_node"]:
                        continue
                    chunk = event["data"]["chunk"]
                    if chunk.content:
                        text_part = chunk.content if isinstance(chunk.content, str) else "".join([b.get("text", "") for b in chunk.content if isinstance(b, dict) and "text" in b])
                        if text_part:
                            current_message_buffer += text_part
                            if "[INTERNAL]" in current_message_buffer:
                                if not mute_stream:
                                    mute_stream = True
                                    await websocket.send_text(json.dumps({"type": "clear_stream"}))
                            
                            if not mute_stream:
                                if current_message_buffer.startswith("[") and len(current_message_buffer) < len("[INTERNAL]"):
                                    # Buffer until we know if it's an internal message or just a bracket
                                    pass
                                else:
                                    await websocket.send_text(json.dumps({"type": "stream", "content": text_part}))
                        
                elif kind == "on_tool_start":
                    print(f"Executing tool: {name}", flush=True)
                    await websocket.send_text(json.dumps({"type": "log", "content": f"⚙️ Executing tool: {name}"}))
                elif kind == "on_tool_end":
                    print(f"Finished tool: {name}", flush=True)
                    await websocket.send_text(json.dumps({"type": "log", "content": f"✅ Finished: {name}"}))
                
                # Reset buffer when a new node starts generating
                elif kind == "on_chat_model_end":
                    current_message_buffer = ""
                    mute_stream = False

            await websocket.send_text(json.dumps({"type": "end"}))
    except WebSocketDisconnect:
        print("Client disconnected")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
