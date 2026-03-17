from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    aws_region: str = "ap-northeast-2"
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    dynamodb_table_name: str = "ChatbotData"
    dynamodb_endpoint_url: Optional[str] = None
    s3_bucket_name: str = "chatbot-conversations"
    cognito_user_pool_id: Optional[str] = None
    cognito_client_id: Optional[str] = None
    jwt_algorithm: str = "RS256"
    skip_auth: bool = False
    allowed_origins: str = "*"
    
    class Config:
        env_file = ".env"

settings = Settings()
