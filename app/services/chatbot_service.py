from datetime import datetime
from app.repositories.chatbot_repository import ChatbotRepository
from app.models.chatbot import ChatMessageRequest, ChatMessageResponse, ChatHistoryResponse, ChatMessage

class ChatbotService:
    def __init__(self):
        self._repository = None

    @property
    def repository(self):
        if self._repository is None:
            self._repository = ChatbotRepository()
        return self._repository

    def send_message(self, request: ChatMessageRequest) -> ChatMessageResponse:
        timestamp = datetime.utcnow().isoformat() + 'Z'
        conversation_id = request.result_id

        bot_message = self._generate_bot_response(request.message)
        bot_timestamp = datetime.utcnow().isoformat() + 'Z'

        history = self.repository.get_conversation(request.cognito_id, conversation_id) or {"messages": []}
        history["messages"].extend([
            {"type": "user", "content": request.message, "timestamp": timestamp},
            {"type": "bot", "content": bot_message, "timestamp": bot_timestamp},
        ])
        history["conversation_id"] = conversation_id
        history["cognito_id"] = request.cognito_id
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

    def _generate_bot_response(self, user_message: str) -> str:
        return "영양제 관련 질문에 대한 답변입니다. 추가 질문이 있으시면 말씀해주세요."
