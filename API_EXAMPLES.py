"""
API Usage Examples

This file demonstrates how to use the implemented APIs.
"""

# Example 1: Login
"""
POST /api/auth/login
Content-Type: application/json

{
  "email": "hong1234@email.com",
  "password": "password123"
}

Response:
{
  "cognito_id": "uuid-string",
  "email": "hong1234@email.com",
  "access_token": "jwt-token",
  "refresh_token": "jwt-token"
}
"""

# Example 2: Get User Info
"""
GET /api/auth/me
Authorization: Bearer {access_token}

Response:
{
  "cognito_id": "uuid-string",
  "email": "hong1234@email.com",
  "created_at": "2024-01-01T00:00:00Z"
}
"""

# Example 3: Get Analysis History
"""
GET /api/analysis/history?cognito_id=uuid-string&limit=10&offset=0
Authorization: Bearer {access_token}

Response:
{
  "total": 3,
  "results": [
    {
      "result_id": 1,
      "cognito_id": "uuid-string",
      "summary_jsonb": {
        "title": "영양제 추천 결과",
        "deficient_nutrients": ["비타민C", "비타민D"],
        "total_gap_count": 2
      },
      "created_at": "2026-02-10T00:00:00Z"
    }
  ]
}
"""

# Example 4: Send Chatbot Message
"""
POST /api/chatbot/message
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "cognito_id": "uuid-string",
  "result_id": "123",
  "message": "비타민C를 언제 먹는게 좋나요?"
}

Response:
{
  "bot_message": "영양제 관련 질문에 대한 답변입니다. 추가 질문이 있으시면 말씀해주세요.",
  "timestamp": "2026-03-09T10:30:05Z"
}
"""

# Example 5: Get Chat History
"""
GET /api/chatbot/history/123?cognito_id=uuid-string
Authorization: Bearer {access_token}

Response:
{
  "result_id": "123",
  "messages": [
    {
      "type": "user",
      "content": "비타민C를 언제 먹는게 좋나요?",
      "timestamp": "2026-03-09T10:30:00Z"
    },
    {
      "type": "bot",
      "content": "영양제 관련 질문에 대한 답변입니다...",
      "timestamp": "2026-03-09T10:30:05Z"
    }
  ]
}
"""
