import asyncio
import base64
import json
import re
import uuid
import os
import logging
import wave
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

# ADK & GenAI Imports
from google.genai import types
from google.genai.types import Modality, AutomaticActivityDetection, RealtimeInputConfig
from google.adk.sessions import InMemorySessionService
from google.adk.agents import LlmAgent, LiveRequest, LiveRequestQueue
from google.adk.runners import Runner, RunConfig

load_dotenv()

# If only GEMINI_API_KEY_BROWSER is set (e.g. on Cloud Run), copy it to GEMINI_API_KEY
# so the ADK's internal genai client can find it for live audio transcription.
if not os.environ.get("GEMINI_API_KEY") and os.environ.get("GEMINI_API_KEY_BROWSER"):
    os.environ["GEMINI_API_KEY"] = os.environ["GEMINI_API_KEY_BROWSER"]

from models import (
    FrontendMessage,
    TextMessageEvent,
    TextMessageContent,
    ActivitySnapshotEvent,
    ActivitySnapshotData,
    RunErrorEvent,
    RunErrorData,
    ScreenshotSnapshotEvent,
    ScreenshotSnapshotData,
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Session Service globally
session_service = InMemorySessionService()

@app.get("/")
def read_root():
    return {"status": "Backend running"}

@app.websocket("/ag-ui")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("Frontend connected to /ag-ui WebSocket")

    # 1. Create session and inject WebSocket into ADK state
    session = session_service.create_session_sync(app_name="ian", user_id="default")
    session.state["active_ws"] = websocket

    system_instruction = (
        "You are a strict, headless UI routing engine. "
        "RULE 1: Wrap all internal reasoning inside <think>...</think> tags. "
        "RULE 2: After the <think> block, output ONLY your final decision. "
        "RULE 3: If the user gives a navigation command, you MUST copy their exact words into the brackets. "
        "EXAMPLES OF CORRECT BEHAVIOR: "
        "User: 'go to amazon.com and search for running shoes' "
        "Your Output: I am navigating now. [NAVIGATE: go to amazon.com and search for running shoes] "
        "User: 'open youtube and find ai videos' "
        "Your Output: I am navigating now. [NAVIGATE: open youtube and find ai videos] "
        "RULE 4: If you hear random noise or an incomplete sentence, output exactly: 'I could not hear the full command.'"
    )

    model_name = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash-native-audio-preview-12-2025")
    
    agent = LlmAgent(
        name="UI_Navigator",
        model=model_name,
        tools=[],  # EMPTY! Prevents the 1008 Google API crash
        instruction=system_instruction
    )
    
    runner = Runner(
        app_name="ian",
        agent=agent,
        session_service=session_service
    )
    
    requests_queue = LiveRequestQueue()

    # Helpers for AG-UI Protocol
    async def send_text_message(role: str, text: str):
        msg = TextMessageEvent(
            data=TextMessageContent(
                id=str(uuid.uuid4()),
                role=role,
                text=text
            )
        )
        await websocket.send_json(msg.model_dump())

    async def send_activity_snapshot(status: str):
        msg = ActivitySnapshotEvent(
            data=ActivitySnapshotData(status=status) # type: ignore
        )
        await websocket.send_json(msg.model_dump())

    # 🚨 RESTORED: The UI Cleaner function
    def clean_for_ui(text: str) -> str:
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'\[NAVIGATE:[^\]]*\]', '', text, flags=re.IGNORECASE)
        text = re.sub(r'\*+', '', text)
        cot_phrases = [
            r"I'm wrestling with.*?\.", r"I'm leaning toward.*?\.", r"I'm still stuck.*?\.",
            r"I've decided on.*?\.", r"I'm initiating.*?\.", r"I am unsure.*?\.",
            r"I'll focus on.*?\.", r"I'll attempt to.*?\.", r"I must ensure.*?\.",
            r"The instructions are.*?\.", r"My instructions are.*?\.", r"Due to the user's input.*?\.",
            r"Given the ambiguity.*?\.", r"The text is barely.*?\.", r"Since the prompt.*?\.",
            r"Though it's barely.*?\.", r"Formulating UI Command.*", r"Interpreting Incomplete Command.*",
            r"Assessing Command Clarity.*", r"Defining the Navigation.*", r"Refining the Action.*",
            r"Processing Incomplete Command.*", r"Consolidating the Navigation.*", r"Interpreting.*?\."
        ]
        for pattern in cot_phrases:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    await send_activity_snapshot("idle")
    
    # 🚨 RESTORED: Thread-safe Browser lock to prevent rate limit explosions
    browser_lock = asyncio.Lock()
    
    async def process_adk_responses():
        print("[DEBUG] process_adk_responses task STARTED execution!")
        full_turn_text = ""
        try:
            live_config = RunConfig(
                response_modalities=[Modality.AUDIO],
                realtime_input_config=RealtimeInputConfig(
                    automatic_activity_detection=AutomaticActivityDetection(disabled=True)
                )
            )
            print(f"[DEBUG] Starting ADK run_live with session_id={session.id}")
            
            async for event in runner.run_live(
                user_id="default",
                session_id=session.id, 
                run_config=live_config,
                live_request_queue=requests_queue
            ):
                # 1. Print User Audio Transcript
                if event.input_transcription and event.input_transcription.text:
                    user_text = event.input_transcription.text.strip()
                    if user_text:
                        print(f"[DEBUG] Input transcription: {user_text}")
                        await send_text_message("user", user_text)
                
                # 2. SILENTLY accumulate Agent output (NO streaming to UI here!)
                if event.output_transcription and event.output_transcription.text:
                    agent_text = event.output_transcription.text.strip()
                    if agent_text:
                        full_turn_text += agent_text + " "
                
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text:
                            full_turn_text += part.text + " "
                                
                # 3. Process the FULL text only when the AI stops talking
                if event.turn_complete:
                    print(f"[DEBUG] Turn complete! AI's full thought was: {full_turn_text}")
                    await send_activity_snapshot("idle")
                    
                    if "[NAVIGATE:" in full_turn_text and "]" in full_turn_text:
                        try:
                            goal = full_turn_text.split("[NAVIGATE:")[1].split("]")[0].strip()
                            print(f"[DEBUG] INTERCEPTED NAVIGATION GOAL: {goal}")
                            
                            # Send ONE clean message to the UI
                            await send_text_message("agent", "I am navigating now.")
                            
                            if browser_lock.locked():
                                print("[DEBUG] Browser lock is held — skipping duplicate navigation!")
                            else:
                                from browser_agent import VisualAutomationAgent
                                import traceback
                                
                                async def run_playwright_task(nav_goal: str):
                                    async with browser_lock:
                                        try:
                                            print(f"[DEBUG] 🔒 Acquired browser lock for: {nav_goal}")
                                            automation_agent = VisualAutomationAgent()
                                            
                                            async def stream_update(b64_img: str, action_text: str):
                                                try:
                                                    await websocket.send_json({
                                                        "type": "ActivitySnapshot", 
                                                        "data": {"activityType": "SCREENSHOT", "content": {"base64": b64_img}}
                                                    })
                                                    await websocket.send_json({
                                                        "type": "TextMessageContent",
                                                        "data": {"role": "agent", "text": f"🤖 {action_text}"}
                                                    })
                                                except Exception as ws_err:
                                                    print(f"[WARN] Failed to send UI update: {ws_err}")

                                            loop = asyncio.get_running_loop()
                                            await asyncio.to_thread(
                                                automation_agent._run_sync_loop, 
                                                nav_goal, 
                                                stream_update,
                                                loop
                                            )
                                            print(f"[DEBUG] 🔓 Playwright task finished for: {nav_goal}")
                                            await send_activity_snapshot("idle")
                                            
                                        except Exception as e:
                                            print(f"[CRITICAL ERROR] Playwright crashed: {e}")
                                            traceback.print_exc()

                                print("[DEBUG] Launching locked Playwright task...")
                                asyncio.create_task(run_playwright_task(goal))
                            
                        except Exception as e:
                            print(f"[ERROR] Failed to parse goal: {e}")
                    else:
                        # Fallback: if it was just chatter or an error, clean it and send it
                        cleaned_final = clean_for_ui(full_turn_text)
                        if cleaned_final:
                            await send_text_message("agent", cleaned_final)

                    # Reset for the next turn
                    full_turn_text = ""
                        
        except asyncio.CancelledError:
            print("[DEBUG] process_adk_responses task CANCELLED!")
        except Exception as e:
            print(f"[CRITICAL ERROR] ADK runner crashed violently: {e}")
            import traceback
            with open("adk_crash.log", "w") as f:
                traceback.print_exc(file=f)

    # 4. Main WebSocket Receive Loop
    audio_buffer = bytearray()
    
    try:
        adk_task = asyncio.create_task(process_adk_responses())
        
        while True:
            try:
                data = await websocket.receive_text()
                message_dict = json.loads(data)
                msg = FrontendMessage(**message_dict)

                if msg.type == "Interrupt" or msg.type == "Cancel":
                    await send_activity_snapshot("idle")
                    await send_text_message("agent", "[Agent interrupted]")

                elif msg.type == "StartSpeaking":
                    # 🚨 RESTORED: Crucial ADK VAD signal to wake up the AI
                    print("[DEBUG] Received StartSpeaking — signaling ADK")
                    requests_queue.send_activity_start()
                    await send_activity_snapshot("listening")

                elif msg.type == "StopSpeaking" or msg.type == "EndOfAudio":
                    print(f"[DEBUG] Received {msg.type} — signaling activity end to ADK")
                    await send_activity_snapshot("navigating")
                    
                    if len(audio_buffer) > 0:
                        with wave.open("debug_output.wav", "wb") as wf:
                            wf.setnchannels(1) 
                            wf.setsampwidth(2) 
                            wf.setframerate(16000) 
                            wf.writeframes(audio_buffer)
                        audio_buffer.clear() 
                    
                    # 🚨 RESTORED: Crucial ADK VAD signal to trigger generation
                    requests_queue.send_activity_end()

                elif msg.type == "AudioChunk":
                    if msg.data and "base64Audio" in msg.data:
                        b64_audio = msg.data["base64Audio"]
                        try:
                            pcm_data = base64.b64decode(b64_audio, validate=True)
                        except (base64.binascii.Error, ValueError):
                            continue
                        
                        if len(pcm_data) == 0:
                            continue
                        
                        audio_buffer.extend(pcm_data)
                        
                        requests_queue.send_realtime(
                            types.Blob(mime_type="audio/pcm;rate=16000", data=pcm_data)
                        )
                        
            except WebSocketDisconnect:
                print("Frontend disconnected inside loop.")
                adk_task.cancel()
                break
            except Exception as loop_err:
                print(f"Error processing message: {loop_err}")

    except Exception as e:
        print(f"WebSocket error: {e}")
        import traceback
        with open("main_crash.log", "w") as f:
            traceback.print_exc(file=f)
    finally:
        print("[DEBUG] WebSocket endpoint closed.")