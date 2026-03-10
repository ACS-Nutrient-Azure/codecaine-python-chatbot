"""
Integration tests for backend API and DynamoDB
Tests: chatbot messaging, history retrieval, analysis history, DB operations
"""
import requests
import json
from datetime import datetime
from uuid import uuid4

BASE_URL = "http://localhost:8000"
TEST_COGNITO_ID = "test-user-123"
TEST_RESULT_ID = "test-result-456"

def test_health():
    """Test API is running"""
    response = requests.get(f"{BASE_URL}/")
    assert response.status_code == 200
    print("✓ API health check passed")

def test_chatbot_send_message():
    """Test sending a chatbot message"""
    payload = {
        "cognito_id": TEST_COGNITO_ID,
        "result_id": TEST_RESULT_ID,
        "message": "비타민C는 언제 먹는게 좋나요?"
    }
    response = requests.post(
        f"{BASE_URL}/api/chatbot/message",
        json=payload,
        headers={"Authorization": "Bearer test-token"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "bot_message" in data
    assert "timestamp" in data
    print(f"✓ Chatbot message sent: {data['bot_message'][:50]}...")

def test_chatbot_history():
    """Test retrieving chatbot history"""
    response = requests.get(
        f"{BASE_URL}/api/chatbot/history/{TEST_RESULT_ID}",
        params={"cognito_id": TEST_COGNITO_ID},
        headers={"Authorization": "Bearer test-token"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "result_id" in data
    assert "messages" in data
    print(f"✓ Chatbot history retrieved: {len(data['messages'])} messages")

def test_analysis_history():
    """Test retrieving analysis history"""
    response = requests.get(
        f"{BASE_URL}/api/analysis/history",
        params={"cognito_id": TEST_COGNITO_ID, "limit": 10},
        headers={"Authorization": "Bearer test-token"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "results" in data
    print(f"✓ Analysis history retrieved: {data['total']} results")

def run_all_tests():
    print("\n=== Backend Integration Tests ===\n")
    try:
        test_health()
        test_chatbot_send_message()
        test_chatbot_history()
        test_analysis_history()
        print("\n✅ All tests passed!\n")
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}\n")
    except requests.exceptions.ConnectionError:
        print("\n❌ Cannot connect to backend. Is it running on port 8000?\n")
    except Exception as e:
        print(f"\n❌ Error: {e}\n")

if __name__ == "__main__":
    run_all_tests()
