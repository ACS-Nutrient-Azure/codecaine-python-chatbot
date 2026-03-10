from datetime import datetime
from uuid import uuid4
from app.repositories.chatbot_repository import ChatbotRepository
from app.models.chatbot import ChatMessageRequest, ChatMessageResponse, ChatHistoryResponse, ChatMessage

class ChatbotService:
    def __init__(self):
        self.repository = ChatbotRepository()
    
    def send_message(self, request: ChatMessageRequest) -> ChatMessageResponse:
        timestamp = datetime.utcnow().isoformat() + 'Z'
        conversation_id = request.result_id
        
        # Save user message
        user_message_id = str(uuid4())
        self.repository.save_message(
            cognito_id=request.cognito_id,
            conversation_id=conversation_id,
            message_id=user_message_id,
            timestamp=timestamp,
            is_bot=0,
            message=request.message
        )
        
        # Generate bot response (placeholder logic)
        bot_message = self._generate_bot_response(request.message)
        bot_timestamp = datetime.utcnow().isoformat() + 'Z'
        bot_message_id = str(uuid4())
        
        # Save bot message
        self.repository.save_message(
            cognito_id=request.cognito_id,
            conversation_id=conversation_id,
            message_id=bot_message_id,
            timestamp=bot_timestamp,
            is_bot=1,
            message=bot_message
        )
        
        return ChatMessageResponse(
            bot_message=bot_message,
            timestamp=bot_timestamp
        )
    
    def get_history(self, result_id: str, cognito_id: str) -> ChatHistoryResponse:
        conversation_id = result_id
        items = self.repository.get_messages_by_conversation(conversation_id)
        
        messages = [
            ChatMessage(
                type="bot" if item['is_bot'] == 1 else "user",
                content=item['message'],
                timestamp=item['created_at']
            )
            for item in sorted(items, key=lambda x: x['created_at'])
        ]
        
        return ChatHistoryResponse(
            result_id=result_id,
            messages=messages
        )
    
    def _generate_bot_response(self, user_message: str) -> str:
        # Placeholder bot logic - replace with actual AI/LLM integration
        return f"영양제 관련 질문에 대한 답변입니다. 추가 질문이 있으시면 말씀해주세요."
