from fastapi import APIRouter, WebSocket, Query, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.services.chatbot_websocket_service import ChatbotWebSocketService
from app.services.chatbot_service import ChatbotService
from app.repositories.chatbot_repository import ChatbotRepository
from app.models.chatbot import ChatMessageRequest, ChatMessageResponse

ws_router = APIRouter(prefix="/ws/chatbot", tags=["chatbot-websocket"])
router = APIRouter(prefix="/api/chatbot", tags=["chatbot"])
_bearer = HTTPBearer()

@ws_router.websocket("/{chat_result_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    chat_result_id: str,
    cognito_id: str = Query(...)
):
    service = ChatbotWebSocketService()
    await service.handle_connection(chat_result_id, cognito_id, websocket)

@router.post("/message", response_model=ChatMessageResponse)
async def send_message(
    request: ChatMessageRequest,
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
):
    try:
        service = ChatbotService()
        return service.send_message(request, credentials.credentials)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/{chat_result_id}")
async def get_chat_history(
    chat_result_id: str,
    cognito_id: str = Query(...)
):
    repository = ChatbotRepository()
    history = repository.get_conversation(cognito_id, chat_result_id)

    if not history:
        return {"chat_result_id": chat_result_id, "messages": []}

    return history
