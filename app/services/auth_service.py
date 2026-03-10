import boto3
from app.core.config import settings
from app.models.auth import LoginRequest, LoginResponse, UserInfoResponse

class AuthService:
    def __init__(self):
        self.cognito = boto3.client('cognito-idp', region_name=settings.aws_region)
    
    def login(self, request: LoginRequest) -> LoginResponse:
        response = self.cognito.initiate_auth(
            ClientId=settings.cognito_client_id,
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': request.email,
                'PASSWORD': request.password
            }
        )
        
        id_token = response['AuthenticationResult']['IdToken']
        access_token = response['AuthenticationResult']['AccessToken']
        refresh_token = response['AuthenticationResult']['RefreshToken']
        
        user_response = self.cognito.get_user(AccessToken=access_token)
        cognito_id = user_response['Username']
        
        return LoginResponse(
            cognito_id=cognito_id,
            email=request.email,
            access_token=access_token,
            refresh_token=refresh_token
        )
    
    def get_user_info(self, token_payload: dict) -> UserInfoResponse:
        return UserInfoResponse(
            cognito_id=token_payload['sub'],
            email=token_payload['email'],
            created_at=token_payload.get('auth_time', '')
        )
