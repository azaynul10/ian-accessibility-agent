import json
import asyncio
import os
from google.adk.agents import LlmAgent
from browser_agent import VisualAutomationAgent

# Notice we removed ToolContext because we are manually intercepting the command from main.py!
async def execute_browser_action(goal: str, ws=None):
    """The exact task the user requested."""
    
    async def stream_browser_update(b64_img: str, action_text: str):
        if ws:
            # 1. Stream the visual frame to the BrowserView component
            await ws.send_text(json.dumps({
                "type": "ActivitySnapshot", 
                "data": {"activityType": "SCREENSHOT", "content": {"base64": b64_img}}
            }))
            # 2. Stream the action description to the TranscriptionFeed
            await ws.send_text(json.dumps({
                "type": "TextMessageContent",
                "data": {"role": "agent", "text": f"🤖 {action_text}"}
            }))

    # Initialize the Playwright thread
    automation_agent = VisualAutomationAgent()
    loop = asyncio.get_running_loop()
    
    print(f"[DEBUG] Offloading browser action to background thread: {goal}")
    
    # Run the loop in a dedicated background thread so we don't block the WebSocket ears
    result = await asyncio.to_thread(
        automation_agent._run_sync_loop, 
        goal, 
        stream_browser_update,
        loop
    )
    
    # When the browser loop finishes, tell the UI to stop the "PROCESSING..." circle
    if ws:
        await ws.send_text(json.dumps({
            "type": "ActivitySnapshot", 
            "data": {"status": "idle"}
        }))

    return result

# Initialize the Root Agent WITHOUT tools to prevent the 1008 Crash!
root_agent = LlmAgent(
    name="UI_Navigator",
    model="gemini-2.5-flash-native-audio-preview-12-2025",
    tools=[], # EMPTY! This is critical to prevent the 1008 crash on the Live API
    instruction=(
        "You are a UI routing engine. When the user asks you to do something, first say "
        "'I am navigating now', and then you MUST output a text block exactly like this: "
        "[NAVIGATE: goal string]. For example: [NAVIGATE: go to wikipedia]."
    )
)