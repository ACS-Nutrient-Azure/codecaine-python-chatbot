# Chatbot 서비스

AI 챗봇 대화와 분석 히스토리 조회를 담당하는 FastAPI 마이크로서비스.
DynamoDB Single Table Design으로 대화 내역을 저장하고, Cognito JWT로 인증한다.

---

## 기술 스택

| 구분 | 기술 |
|------|------|
| 언어 | Python 3.11 |
| 프레임워크 | FastAPI 0.109 |
| DB | AWS DynamoDB (Single Table Design) |
| 인증 | AWS Cognito (RS256 JWT) |
| AWS SDK | boto3 |

---

## 실행

```bash
cd services/chatbot

# 가상환경 생성
python3.11 -m venv .venv
source .venv/bin/activate

# 의존성 설치
pip install -r requirements.txt

# 환경변수 설정
cp .env.example .env
# .env 값 입력

# 서버 시작
uvicorn app.main:app --host 0.0.0.0 --port 8002 --reload
```

---

## 환경변수 (`.env`)

```env
# AWS
AWS_REGION=ap-northeast-2
AWS_ACCESS_KEY_ID=<IAM Access Key>
AWS_SECRET_ACCESS_KEY=<IAM Secret Key>

# DynamoDB
DYNAMODB_TABLE_NAME=ChatbotData
DYNAMODB_ENDPOINT_URL=http://13.125.230.157:8000  # 원격 DynamoDB 엔드포인트

# AWS Cognito
COGNITO_USER_POOL_ID=<User Pool ID>
COGNITO_CLIENT_ID=<App Client ID>
JWT_ALGORITHM=RS256

# 인증 스킵 (개발용 — 프로덕션에서 반드시 false)
SKIP_AUTH=false
```

---

## 프로젝트 구조

```
app/
├── main.py                      # FastAPI 앱 + 라우터 등록
├── api/
│   ├── auth.py                  # /api/auth 엔드포인트
│   ├── chatbot.py               # /api/chatbot 엔드포인트
│   └── analysis.py              # /api/analysis/history 엔드포인트
├── core/
│   ├── config.py                # pydantic-settings 환경변수
│   └── security.py              # Cognito JWT 검증
├── models/
│   ├── auth.py
│   ├── chatbot.py
│   └── analysis.py
├── repositories/
│   ├── dynamodb_repository.py   # DynamoDB 기본 CRUD
│   ├── chatbot_repository.py    # 챗봇 대화 저장/조회
│   └── analysis_repository.py  # 분석 히스토리 조회
└── services/
    ├── auth_service.py
    ├── chatbot_service.py
    └── analysis_service.py
```

---

## API 엔드포인트

### 인증

| 메서드 | 경로 | 인증 | 설명 |
|--------|------|------|------|
| `POST` | `/api/auth/login` | ❌ | 로그인 (Cognito 토큰 검증) |
| `GET` | `/api/auth/me` | ✅ | 현재 유저 정보 조회 |

### 챗봇

| 메서드 | 경로 | 인증 | 설명 |
|--------|------|------|------|
| `POST` | `/api/chatbot/message` | ✅ | 챗봇 메시지 전송 |
| `GET` | `/api/chatbot/history/{result_id}` | ✅ | 특정 분석 결과의 채팅 조회 |

#### `POST /api/chatbot/message`

```json
// Request
{ "cognito_id": "string", "result_id": "string", "message": "string" }

// Response
{ "message_id": "string", "response": "string", "created_at": "2024-01-01T00:00:00" }
```

### 분석 히스토리

| 메서드 | 경로 | 인증 | 설명 |
|--------|------|------|------|
| `GET` | `/api/analysis/history` | ✅ | 분석 히스토리 목록 조회 |

#### `GET /api/analysis/history`

**Query Params** `cognito_id`, `limit` (default: 10), `offset` (default: 0)

```json
{
  "items": [
    { "result_id": 1, "created_at": "2024-01-01T00:00:00", "summary": {} }
  ]
}
```

모든 엔드포인트는 `Authorization: Bearer <JWT>` 헤더 필요 (`SKIP_AUTH=false` 시).

---

## DynamoDB 데이터 구조

Single Table Design. PK/SK 패턴으로 모든 데이터를 하나의 테이블에 저장.

| 데이터 타입 | PK | SK |
|------------|----|----|
| 챗봇 대화 | `USER#<cognito_id>` | `CHAT#<result_id>#<timestamp>` |
| 분석 히스토리 | `USER#<cognito_id>` | `ANALYSIS#<timestamp>` |

---

## IAM 권한

| 권한 | 용도 |
|------|------|
| `dynamodb:GetItem` | 단건 조회 |
| `dynamodb:PutItem` | 저장 |
| `dynamodb:Query` | 목록 조회 (PK 기준) |
| `dynamodb:DeleteItem` | 삭제 |
