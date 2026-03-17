from app.repositories.dynamodb_repository import DynamoDBRepository
from app.repositories.s3_repository import S3Repository

class ChatbotRepository:
    def __init__(self):
        self.db = DynamoDBRepository()
        self.s3 = S3Repository()
    
    def get_messages_by_conversation(self, conversation_id: str):
        gsi_pk = f"CONV#{conversation_id}"
        gsi_sk_prefix = "MSG#"
        return self.db.query_by_gsi(gsi_pk, gsi_sk_prefix)
    
    def save_message(self, cognito_id: str, conversation_id: str, message_id: str, 
                     timestamp: str, is_bot: int, message: str):
        item = {
            'PK': f"USER#{cognito_id}",
            'SK': f"CONV#{conversation_id}#MSG#{timestamp}#{message_id}",
            'GSI1PK': f"CONV#{conversation_id}",
            'GSI1SK': f"MSG#{timestamp}#{message_id}",
            'is_bot': is_bot,
            'message': message,
            'created_at': timestamp
        }
        self.db.put_item(item)

    def save_conversation_to_s3(self, conversation_id: str, data: dict):
        self.s3.save_conversation(conversation_id, data)

    def get_conversation_from_s3(self, conversation_id: str) -> dict:
        return self.s3.get_conversation(conversation_id)
