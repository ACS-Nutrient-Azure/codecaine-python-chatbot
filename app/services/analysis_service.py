import json
from sqlalchemy.orm import Session
from app.repositories.chatbot_pg_repository import ChatbotPgRepository
from app.models.analysis import AnalysisHistoryResponse, AnalysisRecord

class AnalysisService:
    def __init__(self, db: Session):
        self.repository = ChatbotPgRepository(db)

    def get_history(self, cognito_id: str, limit: int, offset: int) -> AnalysisHistoryResponse:
        results = self.repository.get_analysis_history(cognito_id, limit, offset)
        total = self.repository.get_analysis_count(cognito_id)

        items = []
        for result in results:
            summary = {}
            if result.chat_summary:
                try:
                    summary = json.loads(result.chat_summary)
                except (ValueError, TypeError):
                    summary = {"title": result.chat_summary}

            items.append(AnalysisRecord(
                result_id=result.chat_result_id,
                cognito_id=result.cognito_id,
                summary_jsonb=summary,
                created_at=result.created_at.isoformat() if result.created_at else ""
            ))

        return AnalysisHistoryResponse(total=total, results=items)
