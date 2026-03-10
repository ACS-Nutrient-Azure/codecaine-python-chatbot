from pydantic import BaseModel
from typing import List, Literal

class ChatMessageRequest(BaseModel):
    cognito_id: str
    result_id: str
    message: str

class ChatMessageResponse(BaseModel):
    bot_message: str
    timestamp: str

class ChatMessage(BaseModel):
    type: Literal["user", "bot"]
    content: str
    timestamp: str

class ChatHistoryResponse(BaseModel):
    result_id: str
    messages: List[ChatMessage]
