from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt, JWTError
import requests
import os
from functools import lru_cache
from app.core.config import settings

security = HTTPBearer()

@lru_cache()
def get_cognito_public_keys():
    keys_url = f"https://cognito-idp.{settings.aws_region}.amazonaws.com/{settings.cognito_user_pool_id}/.well-known/jwks.json"
    response = requests.get(keys_url)
    response.raise_for_status()
    data = response.json()
    if "keys" not in data:
        raise HTTPException(status_code=500, detail="Failed to retrieve Cognito public keys")
    return data["keys"]

def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)) -> dict:
    token = credentials.credentials
    
    # Skip authentication if in test mode or Cognito not configured
    if settings.skip_auth or not settings.cognito_user_pool_id:
        return {"sub": "test-user", "cognito:username": "test"}
    
    try:
        keys = get_cognito_public_keys()
        headers = jwt.get_unverified_headers(token)
        key = next((k for k in keys if k["kid"] == headers["kid"]), None)
        
        if not key:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        payload = jwt.decode(
            token,
            key,
            algorithms=[settings.jwt_algorithm],
            audience=settings.cognito_client_id
        )
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
