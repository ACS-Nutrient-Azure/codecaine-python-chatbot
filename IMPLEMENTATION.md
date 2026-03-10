# Implementation Documentation

## Overview
Backend implementation for APIs #1, #2, #10, #17, and #18 following the Controller-Service-Repository pattern with DynamoDB Single Table Design.

## Architecture

### Directory Structure
```
codecaine-python-chatbot/
├── app/
│   ├── api/              # Controllers (API endpoints)
│   │   ├── auth.py       # Auth endpoints (#1, #2)
│   │   ├── analysis.py   # Analysis endpoints (#10)
│   │   └── chatbot.py    # Chatbot endpoints (#17, #18)
│   ├── services/         # Business logic
│   │   ├── auth_service.py
│   │   ├── analysis_service.py
│   │   └── chatbot_service.py
│   ├── repositories/     # Data access layer
│   │   ├── dynamodb_repository.py
│   │   ├── analysis_repository.py
│   │   └── chatbot_repository.py
│   ├── models/           # Pydantic schemas
│   │   ├── auth.py
│   │   ├── analysis.py
│   │   └── chatbot.py
│   ├── core/             # Configuration & auth
│   │   ├── config.py
│   │   └── auth.py
│   └── main.py           # FastAPI app
├── requirements.txt
├── .env.example
└── README.md
```

## Implemented APIs

### API #1: POST /api/auth/login
- Authenticates user with AWS Cognito
- Returns access token and user info

### API #2: GET /api/auth/me
- Validates JWT token
- Returns current user information

### API #10: GET /api/analysis/history
- Fetches all analysis records for authenticated user
- Returns result_id, created_at, and summary_jsonb
- Supports pagination with limit and offset parameters

### API #17: POST /api/chatbot/message
- Saves user message to DynamoDB
- Generates bot response
- Saves bot message
- Uses result_id as conversation_id

### API #18: GET /api/chatbot/history/{result_id}
- Queries messages using GSI1
- Returns chronologically sorted messages
- Filters by conversation_id (derived from result_id)

## DynamoDB Design

### Analysis Result Storage
- PK: `USER#{cognito_id}`
- SK: `ANALYSIS#{chat_result_id}`
- Attributes: `chat_summary`, `conversation_id`, `created_at`

### Message Storage
- PK: `USER#{cognito_id}`
- SK: `CONV#{conversation_id}#MSG#{timestamp}#{message_id}`
- GSI1PK: `CONV#{conversation_id}`
- GSI1SK: `MSG#{timestamp}#{message_id}`

### Key Features
- No Scan operations (Query only)
- Efficient conversation retrieval via GSI1
- UUID-based message IDs
- ISO 8601 timestamps

## Configuration
Set these environment variables in `.env`:
- AWS_REGION
- DYNAMODB_TABLE_NAME
- COGNITO_USER_POOL_ID
- COGNITO_CLIENT_ID
- JWT_ALGORITHM
