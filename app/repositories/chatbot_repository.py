from app.repositories.s3_repository import S3Repository

class ChatbotRepository:
    def __init__(self):
        self._s3 = None

    @property
    def s3(self):
        if self._s3 is None:
            self._s3 = S3Repository()
        return self._s3

    def save_conversation(self, cognito_id: str, conversation_id: str, data: dict):
        self.s3.save_chat_history(cognito_id, conversation_id, data)

    def get_conversation(self, cognito_id: str, conversation_id: str) -> dict:
        return self.s3.get_chat_history(cognito_id, conversation_id)
