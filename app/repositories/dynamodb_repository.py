import boto3
from boto3.dynamodb.conditions import Key
from app.core.config import settings

class DynamoDBRepository:
    def __init__(self):
        self._dynamodb = None
        self._table = None

    @property
    def dynamodb(self):
        if self._dynamodb is None:
            endpoint_url = getattr(settings, 'dynamodb_endpoint_url', None)
            self._dynamodb = boto3.resource(
                'dynamodb',
                region_name=settings.aws_region,
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
                endpoint_url=endpoint_url
            )
        return self._dynamodb

    @property
    def table(self):
        if self._table is None:
            self._table = self.dynamodb.Table(settings.dynamodb_table_name)
        return self._table

    def query_by_pk_sk(self, pk: str, sk_prefix: str = None):
        if sk_prefix:
            condition = Key('PK').eq(pk) & Key('SK').begins_with(sk_prefix)
        else:
            condition = Key('PK').eq(pk)
        response = self.table.query(KeyConditionExpression=condition)
        return response.get('Items', [])

    def query_by_gsi(self, gsi_pk: str, gsi_sk_prefix: str = None):
        if gsi_sk_prefix:
            condition = Key('GSI1PK').eq(gsi_pk) & Key('GSI1SK').begins_with(gsi_sk_prefix)
        else:
            condition = Key('GSI1PK').eq(gsi_pk)
        response = self.table.query(
            IndexName='GSI1-Conversations',
            KeyConditionExpression=condition,
        )
        return response.get('Items', [])

    def get_item(self, pk: str, sk: str):
        response = self.table.get_item(Key={'PK': pk, 'SK': sk})
        return response.get('Item')

    def put_item(self, item: dict):
        self.table.put_item(Item=item)
