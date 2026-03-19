import asyncio
import json
from datetime import datetime
from typing import Dict
from fastapi import WebSocket
from app.repositories.s3_repository import S3Repository

class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, chat_result_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[chat_result_id] = websocket

    def disconnect(self, chat_result_id: str):
        if chat_result_id in self.active_connections:
            del self.active_connections[chat_result_id]

    async def send_message(self, chat_result_id: str, message: dict):
        if chat_result_id in self.active_connections:
            websocket = self.active_connections[chat_result_id]
            await websocket.send_json(message)

ws_manager = WebSocketManager()

class ChatbotWebSocketService:
    def __init__(self):
        self.s3_repo = S3Repository()

    async def handle_connection(self, chat_result_id: str, cognito_id: str, websocket: WebSocket):
        await ws_manager.connect(chat_result_id, websocket)
        
        history = self.s3_repo.get_chat_history(cognito_id, chat_result_id)
        if history:
            await websocket.send_json({
                "type": "history",
                "messages": history.get("messages", [])
            })
        
        heartbeat_task = asyncio.create_task(self._heartbeat(websocket))
        
        try:
            while True:
                data = await websocket.receive_json()
                if data.get("type") == "pong":
                    continue
                await self._process_message(chat_result_id, cognito_id, data, websocket)
        except Exception:
            heartbeat_task.cancel()
            ws_manager.disconnect(chat_result_id)
    
    async def _heartbeat(self, websocket: WebSocket):
        try:
            while True:
                await asyncio.sleep(30)
                await websocket.send_json({"type": "ping"})
        except Exception:
            pass

    async def _process_message(self, chat_result_id: str, cognito_id: str, data: dict, websocket: WebSocket):
        user_message = data.get("message", "")
        timestamp = datetime.utcnow().isoformat() + 'Z'
        
        user_msg = {
            "type": "user",
            "content": user_message,
            "timestamp": timestamp
        }
        
        await asyncio.sleep(1.5)
        
        bot_response = self._generate_mock_response(user_message, cognito_id)
        bot_timestamp = datetime.utcnow().isoformat() + 'Z'
        
        bot_msg = {
            "type": "bot",
            "content": bot_response,
            "timestamp": bot_timestamp
        }
        
        await websocket.send_json(bot_msg)
        
        history = self.s3_repo.get_chat_history(cognito_id, chat_result_id) or {"messages": []}
        history["messages"].extend([user_msg, bot_msg])
        history["chat_result_id"] = chat_result_id
        history["cognito_id"] = cognito_id
        
        self.s3_repo.save_chat_history(cognito_id, chat_result_id, history)

    def _generate_mock_response(self, user_message: str, cognito_id: str) -> str:
        return f"[Mock Agent] 사용자({cognito_id})님의 질문 '{user_message}'에 대한 답변입니다. 영양제 관련 추가 질문이 있으시면 말씀해주세요."
