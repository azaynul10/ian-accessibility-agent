from typing import Any, Dict, Literal, Optional
from pydantic import BaseModel

# --- Messages FROM Frontend ---

class FrontendMessage(BaseModel):
    type: str
    data: Optional[Dict[str, Any]] = None

class AudioChunkData(BaseModel):
    base64Audio: str

class TextMessageData(BaseModel):
    text: str

# --- Messages TO Frontend (AG-UI Protocol) ---

class TextMessageContent(BaseModel):
    id: str
    role: Literal["user", "agent"]
    text: str

class TextMessageEvent(BaseModel):
    type: Literal["TextMessageContent"] = "TextMessageContent"
    data: TextMessageContent

class ActivitySnapshotData(BaseModel):
    status: Literal["idle", "listening", "navigating", "awaiting_confirmation", "processing"]

class ActivitySnapshotEvent(BaseModel):
    type: Literal["ActivitySnapshot"] = "ActivitySnapshot"
    data: ActivitySnapshotData

class RunErrorData(BaseModel):
    message: str

class RunErrorEvent(BaseModel):
    type: Literal["RunError"] = "RunError"
    data: RunErrorData

class ScreenshotSnapshotData(BaseModel):
    activityType: Literal["SCREENSHOT"] = "SCREENSHOT"
    content: Dict[str, str]  # {"base64": "<image_data>"}

class ScreenshotSnapshotEvent(BaseModel):
    type: Literal["ActivitySnapshot"] = "ActivitySnapshot"
    data: ScreenshotSnapshotData
