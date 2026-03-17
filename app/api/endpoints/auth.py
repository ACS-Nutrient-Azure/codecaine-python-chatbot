from fastapi import APIRouter, Depends
from app.models.auth import UserInfoResponse
from app.services.auth_service import AuthService
from app.core.security import verify_token

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.get("/me", response_model=UserInfoResponse)
def get_me(token_payload: dict = Depends(verify_token)):
    service = AuthService()
    return service.get_user_info(token_payload)
