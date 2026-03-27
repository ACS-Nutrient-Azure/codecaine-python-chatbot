import json
import redis
from contextlib import contextmanager
from app.core.config import settings

class RedisRepository:
    def __init__(self):
        self.client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            password=settings.redis_password if settings.redis_password else None,
            db=settings.redis_db,
            decode_responses=True,
        )
        self.ttl = 86400  # 24시간 (초 단위)

    def get_conversation(self, cognito_id: str, conversation_id: str) -> dict | None:
        """Redis에서 대화 내역 조회"""
        key = self._make_key(cognito_id, conversation_id)
        data = self.client.get(key)
        return json.loads(data) if data else None

    def save_conversation(self, cognito_id: str, conversation_id: str, data: dict):
        """Redis에 대화 내역 저장 (TTL 24시간)"""
        key = self._make_key(cognito_id, conversation_id)
        self.client.setex(key, self.ttl, json.dumps(data, ensure_ascii=False))

    def delete_conversation(self, cognito_id: str, conversation_id: str):
        """Redis에서 대화 내역 삭제"""
        key = self._make_key(cognito_id, conversation_id)
        self.client.delete(key)

    @contextmanager
    def lock(self, conversation_id: str, timeout: int = 5):
        """conversation_id 단위 분산 락"""
        lock_key = f"lock:chat:{conversation_id}"
        lock = self.client.lock(lock_key, timeout=timeout, blocking_timeout=5)
        try:
            lock.acquire()
            yield
        finally:
            if lock.owned():
                lock.release()

    def _make_key(self, cognito_id: str, conversation_id: str) -> str:
        """Redis 키 생성"""
        return f"chat:{cognito_id}:{conversation_id}"
