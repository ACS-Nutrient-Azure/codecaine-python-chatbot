"""
user 서비스 HTTP 클라이언트.
CODEF 건강검진 + 처방 데이터 조회.
"""
import logging
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)


def get_codef_data(cognito_id: str, token: str) -> dict:
    """
    user 서비스에서 CODEF 데이터 조회.

    Returns:
        {
            "codef_health_data": {...},
            "codef_medication_info": [...]
        }
    """
    url = f"{settings.user_service_url}/api/codef/health-data/{cognito_id}"
    try:
        response = httpx.get(
            url,
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        
        return {
            "codef_health_data": data,
            "codef_medication_info": data.get("medications", []),
        }
    except httpx.HTTPStatusError as e:
        logger.warning(f"[{cognito_id}] user 서비스 CODEF 데이터 조회 실패 (HTTP {e.response.status_code})")
    except Exception as e:
        logger.warning(f"[{cognito_id}] user 서비스 호출 실패: {e}")

    return {"codef_health_data": None, "codef_medication_info": None}
