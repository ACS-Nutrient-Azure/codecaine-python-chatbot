from pydantic import BaseModel
from typing import Optional

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    cognito_id: str
    email: str
    access_token: str
    refresh_token: str

class UserInfoResponse(BaseModel):
    cognito_id: str
    email: str
    created_at: str
