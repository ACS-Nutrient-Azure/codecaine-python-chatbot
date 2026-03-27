# Chatbot Backend

AI 챗봇 대화 및 분석 히스토리 관리 서비스 (FastAPI + WebSocket)

## 개요

사용자와의 실시간 채팅을 WebSocket으로 처리하고, Supervisor Agent를 호출하여 AI 응답을 생성합니다. Redis 캐싱과 S3 영구 저장을 통해 대화 히스토리를 관리합니다.

**주요 역할**:
- WebSocket 기반 실시간 채팅
- Supervisor Agent 호출 및 응답 처리
- Redis 캐싱 (24시간 TTL)
- S3 영구 저장 (세션 종료 시)
- 30분 비활성 타임아웃 관리

## 디렉토리 구조

```
codecaine-python-chatbot/
├── app/
│   ├── __init__.py
│   ├── main.py                          # FastAPI 애플리케이션 진입점
│   ├── api/
│   │   ├── __init__.py
│   │   └── endpoints/
│   │       ├── chatbot.py               # WebSocket 엔드포인트
│   │       └── history.py               # 히스토리 조회 API
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py                    # 환경변수 설정 (Pydantic Settings)
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── chatbot.py                   # Request/Response 스키마
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── redis_repository.py          # Redis 캐시 레이어
│   │   └── chatbot_repository.py        # S3 저장소 레이어
│   └── services/
│       ├── __init__.py
│       ├── chatbot_service.py           # Supervisor Agent 호출 로직
│       └── chatbot_websocket_service.py # WebSocket 세션 관리
├── Dockerfile                           # Docker 이미지 빌드 설정
├── requirements.txt                     # Python 패키지 목록
├── .env.example                         # 환경변수 예시
└── README.md                            # 이 문서
```

## 주요 파일 설명

### `app/api/endpoints/chatbot.py`
- WebSocket `/ws/{conversation_id}` 엔드포인트
- 메시지 수신 및 응답 전송
- 세션 관리 (연결/종료)

### `app/services/chatbot_websocket_service.py`
- WebSocket 세션 관리
- 30분 비활성 타임아웃
- 5분 재연결 grace period
- 세션 종료 시 S3 동기화

### `app/services/chatbot_service.py`
- Supervisor Agent 호출 (`_call_supervisor`)
- 로컬 테스트: HTTP 직접 호출
- AWS 배포: boto3 bedrock-agentcore-runtime 사용
- CODEF 데이터 조회 및 전달

### `app/repositories/redis_repository.py`
- Redis 캐시 CRUD
- 24시간 TTL
- conversation_id 기반 분산 락

### `app/repositories/chatbot_repository.py`
- S3 저장소 CRUD
- Redis 우선 조회 (cache-aside pattern)
- 세션 종료 시 S3 동기화

## 전체 흐름

```
Frontend (WebSocket)
    └─→ /ws/{conversation_id}
            └─→ ChatbotWebSocketService
                    ├─→ Redis에서 히스토리 조회
                    ├─→ ChatbotService._call_supervisor()
                    │       └─→ Supervisor Agent 호출
                    ├─→ Redis에 메시지 저장
                    └─→ [30분 타임아웃 or 연결 종료]
                            └─→ S3에 동기화
```

## API 명세

### WebSocket /ws/{conversation_id}

실시간 채팅 엔드포인트

**연결:**
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/conv-123?token=<jwt>');
```

**메시지 전송:**
```json
{
  "message": "영양제 추천해줘"
}
```

**메시지 수신:**
```json
{
  "type": "message",
  "content": "[섭취 목적] ...",
  "timestamp": "2024-03-27T10:00:00Z"
}
```

**타임아웃 알림:**
```json
{
  "type": "timeout_warning",
  "remaining_seconds": 60
}
```

### GET /api/chatbot/history/{conversation_id}

대화 히스토리 조회

**Response:**
```json
{
  "conversation_id": "conv-123",
  "messages": [
    {
      "role": "user",
      "content": "영양제 추천해줘",
      "timestamp": "2024-03-27T10:00:00Z"
    },
    {
      "role": "assistant",
      "content": "[섭취 목적] ...",
      "timestamp": "2024-03-27T10:00:05Z"
    }
  ]
}
```

## 환경변수 설정

### 필수 환경변수

```bash
# AWS 설정
AWS_REGION=ap-northeast-2

# Cognito
COGNITO_USER_POOL_ID=<User Pool ID>
COGNITO_CLIENT_ID=<Client ID>

# Redis
REDIS_HOST=<ElastiCache 엔드포인트>
REDIS_PORT=6379
REDIS_DB=0

# S3
S3_BUCKET_NAME=<대화 히스토리 버킷>

# Supervisor Agent
SUPERVISOR_AGENT_ARN=<Supervisor Agent ARN>

# User Service
USER_SERVICE_URL=<User Service URL>
```

### 로컬 테스트용 환경변수

```bash
REDIS_HOST=localhost
SUPERVISOR_AGENT_ARN=http://localhost:8001
USER_SERVICE_URL=http://localhost:8000
```

## 로컬 실행

### 1. Redis 실행

```bash
# Docker로 Redis 실행
docker run -d -p 6379:6379 redis:7-alpine
```

### 2. 환경 설정

```bash
# 가상환경 생성
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 패키지 설치
pip install -r requirements.txt

# 환경변수 설정
cp .env.example .env
# .env 파일 편집
```

### 3. Supervisor Agent 실행 (로컬 테스트 시)

```bash
cd ../codecaine-python-supervisoragent
uvicorn app.main:app --reload --port 8001
```

### 4. Chatbot Backend 실행

```bash
uvicorn app.main:app --reload --port 8000
```

### 5. 테스트

```bash
# WebSocket 연결 테스트 (wscat 사용)
npm install -g wscat
wscat -c "ws://localhost:8000/ws/test-conv-123?token=<jwt>"

# 메시지 전송
> {"message": "영양제 추천해줘"}
```

## Docker 빌드 및 실행

```bash
# 이미지 빌드
docker build -t chatbot-backend .

# 컨테이너 실행
docker run -p 8000:8000 --env-file .env chatbot-backend
```

## AWS 배포

### 1. ECR 푸시

```bash
# ECR 로그인
aws ecr get-login-password --region ap-northeast-2 | \
  docker login --username AWS --password-stdin <account-id>.dkr.ecr.ap-northeast-2.amazonaws.com

# 이미지 태그 및 푸시
docker tag chatbot-backend:latest <account-id>.dkr.ecr.ap-northeast-2.amazonaws.com/chatbot-backend:latest
docker push <account-id>.dkr.ecr.ap-northeast-2.amazonaws.com/chatbot-backend:latest
```

### 2. ECS 배포

Terraform 또는 AWS 콘솔로 ECS 서비스 배포

### 3. 환경변수 설정

```bash
AWS_REGION=ap-northeast-2
COGNITO_USER_POOL_ID=<User Pool ID>
REDIS_HOST=<ElastiCache 엔드포인트>
S3_BUCKET_NAME=<버킷명>
SUPERVISOR_AGENT_ARN=<Supervisor Agent ARN>
```

### 4. IAM 권한 설정

ECS Task Role에 다음 권한 필요:
- `s3:GetObject`, `s3:PutObject` (대화 히스토리 버킷)
- `bedrock:InvokeAgent` (Supervisor Agent)
- `cognito-idp:GetUser` (사용자 정보 조회)

## 기술 스택

- **Framework**: FastAPI, WebSocket
- **Cache**: Redis (ElastiCache)
- **Storage**: S3
- **Authentication**: AWS Cognito JWT
- **Agent Communication**: boto3 bedrock-agentcore-runtime

## 주요 기능

### 1. Redis 캐싱
- 24시간 TTL
- Cache-aside pattern
- 분산 락 (conversation_id 기반)

### 2. 세션 관리
- 30분 비활성 타임아웃
- 5분 재연결 grace period
- 타임아웃 1분 전 경고 메시지

### 3. S3 동기화
- 세션 종료 시에만 S3 저장
- 중간 백업 없음 (Redis만 사용)
- 비용 최적화

### 4. CODEF 데이터 통합
- User Service에서 건강검진/복용약 데이터 조회
- Supervisor Agent에 전달

## 문제 해결

### Redis 연결 실패
```bash
# Redis 연결 확인
redis-cli -h <REDIS_HOST> ping

# ElastiCache Security Group 확인
```

### WebSocket 연결 끊김
```bash
# 타임아웃 설정 확인
echo $INACTIVITY_TIMEOUT_SECONDS

# 로그 확인
docker logs <container-id>
```

### Supervisor Agent 호출 실패
```bash
# ARN 확인
echo $SUPERVISOR_AGENT_ARN

# IAM 권한 확인
aws iam get-role-policy --role-name <role-name> --policy-name <policy-name>
```

## 배포 순서

1. **Redis (ElastiCache)** 생성
2. **S3 버킷** 생성
3. **Supervisor Agent** 배포 → ARN 복사
4. **Chatbot Backend** 배포 (ARN 환경변수 설정)
