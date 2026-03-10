from app.repositories.dynamodb_repository import DynamoDBRepository

class AnalysisRepository:
    def __init__(self):
        self.db = DynamoDBRepository()
    
    def get_user_analysis_results(self, cognito_id: str, limit: int = 10):
        pk = f"USER#{cognito_id}"
        sk_prefix = "ANALYSIS#"
        items = self.db.query_by_pk_sk(pk, sk_prefix)
        
        # Sort by created_at descending and limit
        sorted_items = sorted(items, key=lambda x: x.get('created_at', ''), reverse=True)
        return sorted_items[:limit]
