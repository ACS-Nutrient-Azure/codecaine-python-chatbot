from fastapi import APIRouter
from app.api.endpoints import auth, chatbot, analysis

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(chatbot.ws_router)
api_router.include_router(chatbot.router)
api_router.include_router(analysis.router)
