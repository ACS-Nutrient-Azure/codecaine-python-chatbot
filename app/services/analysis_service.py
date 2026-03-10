import json
from app.repositories.analysis_repository import AnalysisRepository
from app.models.analysis import AnalysisHistoryResponse, AnalysisRecord

class AnalysisService:
    def __init__(self):
        self.repository = AnalysisRepository()
    
    def get_history(self, cognito_id: str, limit: int = 10) -> AnalysisHistoryResponse:
        items = self.repository.get_user_analysis_results(cognito_id, limit)
        
        results = []
        for item in items:
            # Extract result_id from SK (format: ANALYSIS#timestamp#result_id)
            sk = item.get('SK', '')
            result_id = int(sk.split('#')[-1]) if '#' in sk else 0
            
            # Parse summary if it's a string
            summary = item.get('chat_summary', {})
            if isinstance(summary, str):
                try:
                    summary = json.loads(summary)
                except:
                    summary = {"title": summary}
            
            results.append(AnalysisRecord(
                result_id=result_id,
                cognito_id=item.get('PK', '').replace('USER#', ''),
                summary_jsonb=summary,
                created_at=item.get('created_at', '')
            ))
        
        return AnalysisHistoryResponse(
            total=len(results),
            results=results
        )
