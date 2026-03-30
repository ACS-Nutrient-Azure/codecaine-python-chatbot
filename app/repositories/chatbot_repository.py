from app.repositories.s3_repository import S3Repository
from app.repositories.redis_repository import RedisRepository

class ChatbotRepository:
    def __init__(self):
        self._s3 = None
        self._redis = None

    @property
    def s3(self):
        if self._s3 is None:
            self._s3 = S3Repository()
        return self._s3

    @property
    def redis(self):
        if self._redis is None:
            self._redis = RedisRepository()
        return self._redis

    def save_conversation(self, cognito_id: str, conversation_id: str, data: dict):
        """Redis에 저장 (락 사용)"""
        with self.redis.lock(conversation_id):
            self.redis.save_conversation(cognito_id, conversation_id, data)

    def get_conversation(self, cognito_id: str, conversation_id: str) -> dict:
        """Redis 우선 조회 → 없으면 S3 조회 후 Redis 캐싱"""
        # Redis 조회
        data = self.redis.get_conversation(cognito_id, conversation_id)
        if data:
            return data
        
        # S3 조회
        data = self.s3.get_chat_history(cognito_id, conversation_id)
        if data:
            # Redis에 캐싱
            self.redis.save_conversation(cognito_id, conversation_id, data)
        return data

    def sync_to_s3(self, cognito_id: str, conversation_id: str):
        """Redis → S3 동기화 (세션 종료 시 호출)"""
        data = self.redis.get_conversation(cognito_id, conversation_id)
        if data:
            self.s3.save_chat_history(cognito_id, conversation_id, data)
            # S3 저장 후 Redis에서 삭제하지 않음 (TTL로 자동 삭제)
