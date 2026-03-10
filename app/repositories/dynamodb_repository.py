import boto3
from app.core.config import settings

class DynamoDBRepository:
    def __init__(self):
        endpoint_url = getattr(settings, 'dynamodb_endpoint_url', None)
        self.dynamodb = boto3.resource(
            'dynamodb', 
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            endpoint_url=endpoint_url
        )
        self.table = self.dynamodb.Table(settings.dynamodb_table_name)
    
    def query_by_pk_sk(self, pk: str, sk_prefix: str = None):
        if sk_prefix:
            response = self.table.query(
                KeyConditionExpression='PK = :pk AND begins_with(SK, :sk)',
                ExpressionAttributeValues={':pk': pk, ':sk': sk_prefix}
            )
        else:
            response = self.table.query(
                KeyConditionExpression='PK = :pk',
                ExpressionAttributeValues={':pk': pk}
            )
        return response.get('Items', [])
    
    def query_by_gsi(self, gsi_pk: str, gsi_sk_prefix: str = None):
        if gsi_sk_prefix:
            response = self.table.query(
                IndexName='GSI1-Conversations',
                KeyConditionExpression='GSI1PK = :pk AND begins_with(GSI1SK, :sk)',
                ExpressionAttributeValues={':pk': gsi_pk, ':sk': gsi_sk_prefix}
            )
        else:
            response = self.table.query(
                IndexName='GSI1-Conversations',
                KeyConditionExpression='GSI1PK = :pk',
                ExpressionAttributeValues={':pk': gsi_pk}
            )
        return response.get('Items', [])
    
    def get_item(self, pk: str, sk: str):
        response = self.table.get_item(Key={'PK': pk, 'SK': sk})
        return response.get('Item')
    
    def put_item(self, item: dict):
        self.table.put_item(Item=item)
