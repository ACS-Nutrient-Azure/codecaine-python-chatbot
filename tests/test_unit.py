"""
Unit Tests — S3Repository storage logic & data transformation
Focus: save_chat_history, get_chat_history, key format, edge cases
"""
import json
import pytest
from unittest.mock import MagicMock, patch
from botocore.exceptions import ClientError


COGNITO_ID = "44780ddc-e081-70a7-899b-dd7b53569880"
RESULT_ID = "1"
BUCKET = "chatbot-conversations"


@pytest.fixture
def s3_repo():
    with patch("app.repositories.s3_repository.boto3.client") as mock_client:
        mock_s3 = MagicMock()
        mock_s3.exceptions.NoSuchKey = ClientError
        mock_client.return_value = mock_s3
        from app.repositories.s3_repository import S3Repository
        repo = S3Repository()
        repo._s3 = mock_s3
        yield repo, mock_s3


# --- save_chat_history ---

def test_save_chat_history_correct_key(s3_repo):
    repo, mock_s3 = s3_repo
    data = {"messages": [{"type": "user", "content": "hello", "timestamp": "2026-01-01T00:00:00Z"}]}
    repo.save_chat_history(COGNITO_ID, RESULT_ID, data)

    mock_s3.put_object.assert_called_once()
    call_kwargs = mock_s3.put_object.call_args[1]
    assert call_kwargs["Key"] == f"chat-history/{COGNITO_ID}/{RESULT_ID}.json"
    assert call_kwargs["Bucket"] == BUCKET


def test_save_chat_history_body_is_valid_json(s3_repo):
    repo, mock_s3 = s3_repo
    data = {"messages": [{"type": "bot", "content": "비타민 D 답변", "timestamp": "2026-01-01T00:00:01Z"}]}
    repo.save_chat_history(COGNITO_ID, RESULT_ID, data)

    body = mock_s3.put_object.call_args[1]["Body"]
    parsed = json.loads(body)
    assert parsed["messages"][0]["content"] == "비타민 D 답변"


def test_save_chat_history_empty_messages(s3_repo):
    repo, mock_s3 = s3_repo
    repo.save_chat_history(COGNITO_ID, RESULT_ID, {"messages": []})
    body = json.loads(mock_s3.put_object.call_args[1]["Body"])
    assert body["messages"] == []


# --- get_chat_history ---

def test_get_chat_history_returns_parsed_data(s3_repo):
    repo, mock_s3 = s3_repo
    payload = {"messages": [{"type": "user", "content": "test", "timestamp": "2026-01-01T00:00:00Z"}]}
    mock_s3.get_object.return_value = {
        "Body": MagicMock(read=lambda: json.dumps(payload).encode("utf-8"))
    }

    result = repo.get_chat_history(COGNITO_ID, RESULT_ID)
    assert result["messages"][0]["content"] == "test"


def test_get_chat_history_no_such_key_returns_none(s3_repo):
    repo, mock_s3 = s3_repo
    mock_s3.exceptions.NoSuchKey = Exception
    mock_s3.get_object.side_effect = mock_s3.exceptions.NoSuchKey("not found")

    result = repo.get_chat_history(COGNITO_ID, "nonexistent")
    assert result is None


def test_get_chat_history_unexpected_error_returns_none(s3_repo):
    repo, mock_s3 = s3_repo
    mock_s3.get_object.side_effect = RuntimeError("connection error")

    result = repo.get_chat_history(COGNITO_ID, RESULT_ID)
    assert result is None


# --- data transformation (AnalysisService) ---

def test_analysis_service_plain_text_summary_wrapped():
    """chat_summary that is plain text (not JSON) should be wrapped as {"title": ...}"""
    from unittest.mock import MagicMock
    from app.services.analysis_service import AnalysisService

    db = MagicMock()
    service = AnalysisService(db)

    mock_result = MagicMock()
    mock_result.chat_result_id = 1
    mock_result.cognito_id = COGNITO_ID
    mock_result.chat_summary = "비타민 D 부족"
    mock_result.created_at = None

    service.repository.get_analysis_history = MagicMock(return_value=[mock_result])
    service.repository.get_analysis_count = MagicMock(return_value=1)

    response = service.get_history(COGNITO_ID, 10, 0)
    assert response.results[0].summary_jsonb == {"title": "비타민 D 부족"}


def test_analysis_service_json_summary_parsed():
    """chat_summary that is valid JSON should be parsed as-is"""
    from unittest.mock import MagicMock
    from app.services.analysis_service import AnalysisService

    db = MagicMock()
    service = AnalysisService(db)

    mock_result = MagicMock()
    mock_result.chat_result_id = 2
    mock_result.cognito_id = COGNITO_ID
    mock_result.chat_summary = json.dumps({"title": "분석 완료", "score": 85})
    mock_result.created_at = None

    service.repository.get_analysis_history = MagicMock(return_value=[mock_result])
    service.repository.get_analysis_count = MagicMock(return_value=1)

    response = service.get_history(COGNITO_ID, 10, 0)
    assert response.results[0].summary_jsonb["score"] == 85


def test_analysis_service_empty_history():
    from unittest.mock import MagicMock
    from app.services.analysis_service import AnalysisService

    db = MagicMock()
    service = AnalysisService(db)
    service.repository.get_analysis_history = MagicMock(return_value=[])
    service.repository.get_analysis_count = MagicMock(return_value=0)

    response = service.get_history(COGNITO_ID, 10, 0)
    assert response.total == 0
    assert response.results == []
