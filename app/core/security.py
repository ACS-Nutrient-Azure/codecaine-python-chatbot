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
    if not settings.cognito_user_pool_id:
        raise HTTPException(status_code=500, detail="Cognito user pool not configured")
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
        # kid가 없는 토큰(HS256 dev 토큰 등)은 Cognito 키와 매칭 불가 → 401
        kid = headers.get("kid")
        key = next((k for k in keys if k["kid"] == kid), None) if kid else None

        if not key:
            raise HTTPException(status_code=401, detail="Invalid token")

        payload = jwt.decode(
            token,
            key,
            algorithms=[settings.jwt_algorithm],
            audience=settings.cognito_client_id
        )
        return payload
    except HTTPException:
        raise
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
