from fastapi import APIRouter, Depends, Query
from app.models.chatbot import ChatMessageRequest, ChatMessageResponse, ChatHistoryResponse
from app.services.chatbot_service import ChatbotService
from app.core.auth import verify_token

router = APIRouter(prefix="/api/chatbot", tags=["chatbot"])

@router.post("/message", response_model=ChatMessageResponse)
def send_message(request: ChatMessageRequest, token_payload: dict = Depends(verify_token)):
    service = ChatbotService()
    return service.send_message(request)

@router.get("/history/{result_id}", response_model=ChatHistoryResponse)
def get_history(
    result_id: str,
    cognito_id: str = Query(...),
    token_payload: dict = Depends(verify_token)
):
    service = ChatbotService()
    return service.get_history(result_id, cognito_id)
