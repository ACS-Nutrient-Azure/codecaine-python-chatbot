from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.db_models import ChatbotAnalysisResult

class ChatbotPgRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_analysis_history(self, cognito_id: str, limit: int, offset: int):
        return (
            self.db.query(ChatbotAnalysisResult)
            .filter(ChatbotAnalysisResult.cognito_id == cognito_id)
            .order_by(desc(ChatbotAnalysisResult.created_at))
            .limit(limit)
            .offset(offset)
            .all()
        )

    def get_analysis_count(self, cognito_id: str) -> int:
        return (
            self.db.query(ChatbotAnalysisResult)
            .filter(ChatbotAnalysisResult.cognito_id == cognito_id)
            .count()
        )

    def get_analysis_result(self, chat_result_id: int):
        return (
            self.db.query(ChatbotAnalysisResult)
            .filter(ChatbotAnalysisResult.chat_result_id == chat_result_id)
            .first()
        )
