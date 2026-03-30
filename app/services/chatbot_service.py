import json
import boto3
from datetime import datetime
from app.repositories.chatbot_repository import ChatbotRepository
from app.models.chatbot import ChatMessageRequest, ChatMessageResponse, ChatHistoryResponse, ChatMessage
from app.core.config import settings
from app.services.user_client import get_codef_data

class ChatbotService:
    def __init__(self):
        self._repository = None
        self._boto_session = boto3.Session(region_name=settings.aws_region)

    @property
    def repository(self):
        if self._repository is None:
            self._repository = ChatbotRepository()
        return self._repository

    def send_message(self, request: ChatMessageRequest, token: str) -> ChatMessageResponse:
        timestamp = datetime.utcnow().isoformat() + 'Z'
        conversation_id = request.result_id

        history = self.repository.get_conversation(request.cognito_id, conversation_id) or {"messages": []}
        history["messages"].append({"type": "user", "content": request.message, "timestamp": timestamp})
        
        chat_history = self._build_chat_history(history["messages"])
        codef_data = get_codef_data(request.cognito_id, token)
        bot_message = self._call_supervisor(
            request.cognito_id,
            conversation_id,
            chat_history,
            codef_data["codef_health_data"],
            codef_data["codef_medication_info"]
        )
        bot_timestamp = datetime.utcnow().isoformat() + 'Z'

        history["messages"].append({"type": "bot", "content": bot_message, "timestamp": bot_timestamp})
        history["conversation_id"] = conversation_id
        history["cognito_id"] = request.cognito_id
        history["last_activity"] = bot_timestamp  # 마지막 활동 시간 추적
        self.repository.save_conversation(request.cognito_id, conversation_id, history)

        return ChatMessageResponse(bot_message=bot_message, timestamp=bot_timestamp)

    def get_history(self, result_id: str, cognito_id: str) -> ChatHistoryResponse:
        data = self.repository.get_conversation(cognito_id, result_id)
        if not data:
            return ChatHistoryResponse(result_id=result_id, messages=[])
        messages = [
            ChatMessage(type=msg['type'], content=msg['content'], timestamp=msg['timestamp'])
            for msg in data.get('messages', [])
        ]
        return ChatHistoryResponse(result_id=result_id, messages=messages)

    def end_session(self, cognito_id: str, conversation_id: str):
        """세션 종료 시 Redis → S3 동기화"""
        self.repository.sync_to_s3(cognito_id, conversation_id)

    def _build_chat_history(self, messages: list) -> str:
        lines = []
        for msg in messages:
            role = "사용자" if msg["type"] == "user" else "봇"
            lines.append(f"{role}: {msg['content']}")
        return "\n".join(lines)

    def _call_supervisor(
        self,
        cognito_id: str,
        chat_result_id: str,
        chat_history: str,
        codef_health_data: dict | None,
        codef_medication_info: list | None
    ) -> str:
        if settings.supervisor_agent_arn == "placeholder":
            return "Supervisor Agent ARN이 설정되지 않았습니다."
        
        payload = {
            "cognito_id": cognito_id,
            "chat_result_id": int(chat_result_id),
            "codef_health_data": codef_health_data,
            "codef_medication_info": codef_medication_info,
            "chat_history": chat_history,
        }
        
        # HTTP URL이면 직접 호출 (로컬 테스트용)
        if settings.supervisor_agent_arn.startswith("http"):
            import httpx
            response = httpx.post(
                settings.supervisor_agent_arn + "/invocations",
                json=payload,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json().get("response", "")
        
        # AgentCore ARN이면 boto3 호출 (실제 배포용)
        client = self._boto_session.client("bedrock-agentcore")
        response = client.invoke_agent_runtime(
            agentRuntimeArn=settings.supervisor_agent_arn,
            payload=json.dumps(payload, ensure_ascii=False),
        )
        raw = response["response"].read()
        result = json.loads(raw)
        return result.get("response", "")
