import json
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from botocore.exceptions import ClientError  # 추가

COGNITO_ID = "44780ddc-e081-70a7-899b-dd7b53569880"
RESULT_ID = "1"

@pytest.fixture(scope="module")
def client():
    # 1. boto3 client 패치
    with patch("app.repositories.s3_repository.boto3.client") as mock_boto:
        mock_s3 = MagicMock()
        
        # 2. NoSuchKey 예외를 실제 에러 클래스로 모킹 (매우 중요)
        # S3Repository에서 except self.s3.exceptions.NoSuchKey 구문을 통과하게 해줍니다.
        mock_s3.exceptions.NoSuchKey = ClientError 
        mock_boto.return_value = mock_s3

        from app.main import app
        
        # 3. TestClient를 with 없이 직접 생성 (TypeError 우회 핵심)
        c = TestClient(app)
        
        # mock_s3를 테스트 코드에서 쉽게 쓰기 위해 등록
        c._mock_s3 = mock_s3
        
        yield c
        # 테스트 종료 후 별도 처리가 필요하다면 여기서 수행 (보통은 생략 가능)

# --- 이하 테스트 함수들은 그대로 유지하되, client._mock_s3.exceptions.NoSuchKey를 활용 ---

def test_analysis_history_returns_seeded_record(client):
    res = client.get(
        f"/api/chatbot/analysis/history?cognito_id={COGNITO_ID}",
        headers={"Authorization": "Bearer dummy"}
    )
    assert res.status_code == 200
    body = res.json()
    assert body["total"] >= 1
    assert body["results"][0]["cognito_id"] == COGNITO_ID

def test_analysis_history_unknown_user_returns_empty(client):
    res = client.get(
        "/api/chatbot/analysis/history?cognito_id=00000000-0000-0000-0000-000000000000",
        headers={"Authorization": "Bearer dummy"}
    )
    assert res.status_code == 200
    assert res.json()["total"] == 0

def test_chat_history_empty_on_first_call(client):
    # 이제 NoSuchKey가 실제 에러 클래스(ClientError)이므로 정상 작동함
    client._mock_s3.get_object.side_effect = client._mock_s3.exceptions.NoSuchKey
    res = client.get(
        f"/api/chatbot/history/{RESULT_ID}?cognito_id={COGNITO_ID}",
        headers={"Authorization": "Bearer dummy"}
    )
    assert res.status_code == 200
    assert res.json()["messages"] == []

# ... (나머지 websocket 테스트 함수들도 그대로 유지) ...


# --- WebSocket: message flow → saved to S3 ---

def test_websocket_receives_bot_reply(client):
    client._mock_s3.get_object.side_effect = client._mock_s3.exceptions.NoSuchKey

    with client.websocket_connect(
        f"/ws/chatbot/{RESULT_ID}?cognito_id={COGNITO_ID}"
    ) as ws:
        ws.send_json({"type": "message", "message": "비타민 D 얼마나 먹어야 하나요?"})
        response = ws.receive_json()
        assert response["type"] == "bot"
        assert "content" in response


def test_websocket_saves_to_s3_after_message(client):
    client._mock_s3.get_object.side_effect = client._mock_s3.exceptions.NoSuchKey
    client._mock_s3.put_object.reset_mock()

    with client.websocket_connect(
        f"/ws/chatbot/{RESULT_ID}?cognito_id={COGNITO_ID}"
    ) as ws:
        ws.send_json({"type": "message", "message": "오메가3 추천해주세요"})
        ws.receive_json()  # bot reply

    client._mock_s3.put_object.assert_called_once()
    saved_body = json.loads(client._mock_s3.put_object.call_args[1]["Body"])
    messages = saved_body["messages"]
    assert any(m["type"] == "user" for m in messages)
    assert any(m["type"] == "bot" for m in messages)


def test_websocket_history_loaded_on_connect(client):
    existing = {
        "chat_result_id": RESULT_ID,
        "cognito_id": COGNITO_ID,
        "messages": [{"type": "user", "content": "이전 메시지", "timestamp": "2026-01-01T00:00:00Z"}]
    }
    client._mock_s3.get_object.side_effect = None
    client._mock_s3.get_object.return_value = {
        "Body": MagicMock(read=lambda: json.dumps(existing).encode("utf-8"))
    }

    with client.websocket_connect(
        f"/ws/chatbot/{RESULT_ID}?cognito_id={COGNITO_ID}"
    ) as ws:
        msg = ws.receive_json()
        assert msg["type"] == "history"
        assert msg["messages"][0]["content"] == "이전 메시지"
