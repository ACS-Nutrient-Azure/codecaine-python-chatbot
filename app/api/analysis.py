from fastapi import APIRouter, Depends, Query
from app.models.analysis import AnalysisHistoryResponse
from app.services.analysis_service import AnalysisService
from app.core.auth import verify_token

router = APIRouter(prefix="/api/analysis", tags=["analysis"])

@router.get("/history", response_model=AnalysisHistoryResponse)
def get_history(
    cognito_id: str = Query(...),
    limit: int = Query(10),
    offset: int = Query(0),
    token_payload: dict = Depends(verify_token)
):
    service = AnalysisService()
    return service.get_history(cognito_id, limit)
