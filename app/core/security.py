from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt, JWTError
import requests
import time
from app.core.config import settings

security = HTTPBearer()

# 성공한 키만 캐시 (예외는 캐시하지 않음), TTL 1시간
_cognito_keys_cache: dict = {"keys": None, "expires_at": 0}
_CACHE_TTL = 3600

def get_cognito_public_keys():
    now = time.time()
    if _cognito_keys_cache["keys"] is not None and now < _cognito_keys_cache["expires_at"]:
        return _cognito_keys_cache["keys"]

    if not settings.cognito_user_pool_id:
        raise HTTPException(status_code=500, detail="Cognito user pool not configured")

    keys_url = (
        f"https://cognito-idp.{settings.aws_region}.amazonaws.com"
        f"/{settings.cognito_user_pool_id}/.well-known/jwks.json"
    )
    response = requests.get(keys_url, timeout=5)
    response.raise_for_status()
    data = response.json()
    if "keys" not in data:
        raise HTTPException(status_code=500, detail="Failed to retrieve Cognito public keys")

    # 성공한 경우에만 캐시 저장
    _cognito_keys_cache["keys"] = data["keys"]
    _cognito_keys_cache["expires_at"] = now + _CACHE_TTL
    return _cognito_keys_cache["keys"]

def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)) -> dict:
    token = credentials.credentials

    if settings.skip_auth or not settings.cognito_user_pool_id:
        return {"sub": "test-user", "cognito:username": "test"}

    try:
        keys = get_cognito_public_keys()
        headers = jwt.get_unverified_headers(token)
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
