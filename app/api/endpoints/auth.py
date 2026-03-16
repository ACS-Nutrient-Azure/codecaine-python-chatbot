from fastapi import APIRouter, Depends
from app.models.auth import LoginRequest, LoginResponse, UserInfoResponse
from app.services.auth_service import AuthService
from app.core.security import verify_token

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest):
    service = AuthService()
    return service.login(request)

@router.get("/me", response_model=UserInfoResponse)
def get_me(token_payload: dict = Depends(verify_token)):
    service = AuthService()
    return service.get_user_info(token_payload)
