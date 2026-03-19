from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.models.analysis import AnalysisHistoryResponse
from app.services.analysis_service import AnalysisService
from app.core.security import verify_token
from app.core.database import get_db

router = APIRouter(prefix="/api/chatbot/analysis", tags=["analysis"])

@router.get("/history", response_model=AnalysisHistoryResponse)
def get_history(
    cognito_id: str = Query(...),
    limit: int = Query(10),
    offset: int = Query(0),
    token_payload: dict = Depends(verify_token),
    db: Session = Depends(get_db)
):
    service = AnalysisService(db)
    return service.get_history(cognito_id, limit, offset)
