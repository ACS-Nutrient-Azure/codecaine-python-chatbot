import boto3
import json
from app.core.config import settings

class S3Repository:
    def __init__(self):
        self.s3 = boto3.client(
            's3',
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key
        )
        self.bucket = settings.s3_bucket_name

    def save_conversation(self, conversation_id: str, data: dict):
        key = f"conversations/{conversation_id}.json"
        self.s3.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=json.dumps(data, ensure_ascii=False),
            ContentType='application/json'
        )

    def get_conversation(self, conversation_id: str) -> dict:
        key = f"conversations/{conversation_id}.json"
        try:
            response = self.s3.get_object(Bucket=self.bucket, Key=key)
            return json.loads(response['Body'].read().decode('utf-8'))
        except self.s3.exceptions.NoSuchKey:
            return None
        except Exception:
            return None
