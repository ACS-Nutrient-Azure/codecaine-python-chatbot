from pydantic import BaseModel
from typing import List, Dict, Any

class AnalysisSummary(BaseModel):
    title: str
    deficient_nutrients: List[str] = []
    total_gap_count: int = 0

class AnalysisRecord(BaseModel):
    result_id: int
    cognito_id: str
    summary_jsonb: Dict[str, Any]
    created_at: str

class AnalysisHistoryResponse(BaseModel):
    total: int
    results: List[AnalysisRecord]
