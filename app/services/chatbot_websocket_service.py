import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict
from fastapi import WebSocket
from app.repositories.chatbot_repository import ChatbotRepository

class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.session_timers: Dict[str, asyncio.Task] = {}  # 세션 타이머
        self.grace_timers: Dict[str, asyncio.Task] = {}    # grace period 타이머

    async def connect(self, chat_result_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[chat_result_id] = websocket
        # 기존 grace period 타이머 취소
        if chat_result_id in self.grace_timers:
            self.grace_timers[chat_result_id].cancel()
            del self.grace_timers[chat_result_id]

    def disconnect(self, chat_result_id: str, cognito_id: str, repository: ChatbotRepository):
        """연결 끊김 시 5분 grace period 시작"""
        if chat_result_id in self.active_connections:
            del self.active_connections[chat_result_id]
        
        # 세션 타이머 취소
        if chat_result_id in self.session_timers:
            self.session_timers[chat_result_id].cancel()
            del self.session_timers[chat_result_id]
        
        # 5분 grace period 시작
        task = asyncio.create_task(self._grace_period(chat_result_id, cognito_id, repository))
        self.grace_timers[chat_result_id] = task

    async def _grace_period(self, chat_result_id: str, cognito_id: str, repository: ChatbotRepository):
        """5분 대기 후 세션 종료"""
        try:
            await asyncio.sleep(300)  # 5분
            # 재연결 안 됐으면 세션 종료
            if chat_result_id not in self.active_connections:
                repository.sync_to_s3(cognito_id, chat_result_id)
                if chat_result_id in self.grace_timers:
                    del self.grace_timers[chat_result_id]
        except asyncio.CancelledError:
            pass

    async def send_message(self, chat_result_id: str, message: dict):
        if chat_result_id in self.active_connections:
            websocket = self.active_connections[chat_result_id]
            await websocket.send_json(message)

    def reset_session_timer(self, chat_result_id: str, cognito_id: str, repository: ChatbotRepository):
        """30분 무활동 타이머 리셋"""
        # 기존 타이머 취소
        if chat_result_id in self.session_timers:
            self.session_timers[chat_result_id].cancel()
        
        # 새 타이머 시작
        task = asyncio.create_task(self._session_timeout(chat_result_id, cognito_id, repository))
        self.session_timers[chat_result_id] = task

    async def _session_timeout(self, chat_result_id: str, cognito_id: str, repository: ChatbotRepository):
        """30분 무활동 시 세션 종료"""
        try:
            await asyncio.sleep(1800)  # 30분
            # 세션 종료 + S3 동기화
            repository.sync_to_s3(cognito_id, chat_result_id)
            if chat_result_id in self.active_connections:
                websocket = self.active_connections[chat_result_id]
                await websocket.send_json({"type": "session_timeout"})
                await websocket.close()
                del self.active_connections[chat_result_id]
            if chat_result_id in self.session_timers:
                del self.session_timers[chat_result_id]
        except asyncio.CancelledError:
            pass

ws_manager = WebSocketManager()

class ChatbotWebSocketService:
    def __init__(self):
        self.repository = ChatbotRepository()

    async def handle_connection(self, chat_result_id: str, cognito_id: str, websocket: WebSocket, token: str = None):
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            await ws_manager.connect(chat_result_id, websocket)
            logger.info(f"WebSocket connected: chat_result_id={chat_result_id}, cognito_id={cognito_id}")
            
            # 대화 내역 로드 (Redis → S3)
            try:
                history = self.repository.get_conversation(cognito_id, chat_result_id)
                if history:
                    await websocket.send_json({
                        "type": "history",
                        "messages": history.get("messages", [])
                    })
                    logger.info(f"History loaded: {len(history.get('messages', []))} messages")
            except Exception as e:
                logger.error(f"Failed to load history: {e}", exc_info=True)
            
            # 30분 무활동 타이머 시작
            ws_manager.reset_session_timer(chat_result_id, cognito_id, self.repository)
            
            heartbeat_task = asyncio.create_task(self._heartbeat(websocket))
            
            try:
                while True:
                    data = await websocket.receive_json()
                    logger.info(f"Received message: {data}")
                    if data.get("type") == "pong":
                        continue
                    # 메시지 수신 시 타이머 리셋
                    ws_manager.reset_session_timer(chat_result_id, cognito_id, self.repository)
                    await self._process_message(chat_result_id, cognito_id, data, websocket, token)
            except Exception as e:
                logger.error(f"Error in message loop: {e}", exc_info=True)
                heartbeat_task.cancel()
                ws_manager.disconnect(chat_result_id, cognito_id, self.repository)
        except Exception as e:
            logger.error(f"Fatal error in handle_connection: {e}", exc_info=True)
            raise
    
    async def _heartbeat(self, websocket: WebSocket):
        try:
            while True:
                await asyncio.sleep(30)
                await websocket.send_json({"type": "ping"})
        except Exception:
            pass

    async def _process_message(self, chat_result_id: str, cognito_id: str, data: dict, websocket: WebSocket, token: str = None):
        user_message = data.get("message", "")
        timestamp = datetime.utcnow().isoformat() + 'Z'
        
        user_msg = {
            "type": "user",
            "content": user_message,
            "timestamp": timestamp
        }
        
        # 사용자 메시지 먼저 Redis에 저장
        history = self.repository.get_conversation(cognito_id, chat_result_id) or {"messages": []}
        history["messages"].append(user_msg)
        history["chat_result_id"] = chat_result_id
        history["cognito_id"] = cognito_id
        history["last_activity"] = timestamp
        self.repository.save_conversation(cognito_id, chat_result_id, history)
        
        # Supervisor Agent 호출
        from app.services.chatbot_service import ChatbotService
        from app.services.user_client import get_codef_data
        
        # CODEF 데이터 가져오기 (토큰 있으면)
        if token:
            codef_data = await asyncio.to_thread(get_codef_data, cognito_id, token)
        else:
            codef_data = {"codef_health_data": None, "codef_medication_info": None}
        
        # 현재 사용자 메시지만 전달 (이전 대화는 AgentCore Memory가 관리)
        chat_history_text = f"사용자: {user_message}"
        
        # Supervisor 호출
        service = ChatbotService()
        bot_response = service._call_supervisor(
            cognito_id,
            chat_result_id,
            chat_history_text,
            codef_data.get("codef_health_data"),
            codef_data.get("codef_medication_info")
        )
        
        bot_timestamp = datetime.utcnow().isoformat() + 'Z'
        
        bot_msg = {
            "type": "bot",
            "content": bot_response,
            "timestamp": bot_timestamp
        }
        
        await websocket.send_json(bot_msg)
        
        # 봇 메시지 Redis에 저장
        history["messages"].append(bot_msg)
        history["last_activity"] = bot_timestamp
        self.repository.save_conversation(cognito_id, chat_result_id, history)

    def _build_chat_history(self, messages: list) -> str:
        lines = []
        for msg in messages:
            role = "사용자" if msg["type"] == "user" else "봇"
            lines.append(f"{role}: {msg['content']}")
        return "\n".join(lines)
