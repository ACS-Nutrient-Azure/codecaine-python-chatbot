# Codecaine Chatbot Backend

FastAPI-based chatbot service for nutrient recommendation system.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your AWS credentials
```

3. Run the server:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

- `POST /api/auth/login` - User login
- `GET /api/auth/me` - Get current user info
- `GET /api/analysis/history` - Get analysis history
- `POST /api/chatbot/message` - Send chatbot message
- `GET /api/chatbot/history/{result_id}` - Get chat history

## Architecture

- **Controller-Service-Repository** pattern
- **DynamoDB Single Table Design** with PK/SK/GSI1
- **JWT Authentication** via AWS Cognito
