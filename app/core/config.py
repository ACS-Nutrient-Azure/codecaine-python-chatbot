from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    db_host: str
    db_port: int = 5432
    db_name: str
    db_user: str
    db_password: str
    
    aws_region: str = "ap-northeast-2"
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    s3_bucket_name: str = "chatbot-conversations"
    
    cognito_user_pool_id: Optional[str] = None
    cognito_client_id: Optional[str] = None
    jwt_algorithm: str = "RS256"
    skip_auth: bool = False
    allowed_origins: str = "*"
    
    supervisor_agent_arn: str = "placeholder"
    user_service_url: str = "http://localhost:8000"
    
    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str = ""
    redis_db: int = 0
    
    class Config:
        env_file = ".env"

settings = Settings()
