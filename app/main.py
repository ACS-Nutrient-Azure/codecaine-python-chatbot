from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.router import api_router
from app.core.config import settings

app = FastAPI(title="Codecaine Chatbot API", version="1.0.0")

_allowed_origins = (
    [o.strip() for o in settings.allowed_origins.split(",") if o.strip()]
    if getattr(settings, "allowed_origins", None)
    else ["*"]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

@app.get("/")
def root():
    return {"message": "Codecaine Chatbot API"}

@app.get("/health")
def health():
    return {"status": "ok"}
