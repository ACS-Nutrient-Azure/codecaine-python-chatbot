from pydantic import BaseModel

class UserInfoResponse(BaseModel):
    cognito_id: str
    email: str
    created_at: str
