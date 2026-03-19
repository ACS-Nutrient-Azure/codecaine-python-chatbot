from fastapi import APIRouter, WebSocket, Query
from app.services.chatbot_websocket_service import ChatbotWebSocketService
from app.repositories.s3_repository import S3Repository

ws_router = APIRouter(prefix="/ws/chatbot", tags=["chatbot-websocket"])
router = APIRouter(prefix="/api/chatbot", tags=["chatbot"])

@ws_router.websocket("/{chat_result_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    chat_result_id: str,
    cognito_id: str = Query(...)
):
    service = ChatbotWebSocketService()
    await service.handle_connection(chat_result_id, cognito_id, websocket)

@router.get("/history/{chat_result_id}")
async def get_chat_history(
    chat_result_id: str,
    cognito_id: str = Query(...)
):
    s3_repo = S3Repository()
    history = s3_repo.get_chat_history(cognito_id, chat_result_id)

    if not history:
        return {"chat_result_id": chat_result_id, "messages": []}

    return history
