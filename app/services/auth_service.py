from app.models.auth import UserInfoResponse

class AuthService:
    def get_user_info(self, token_payload: dict) -> UserInfoResponse:
        return UserInfoResponse(
            cognito_id=token_payload['sub'],
            email=token_payload['email'],
            created_at=str(token_payload.get('auth_time', ''))
        )
