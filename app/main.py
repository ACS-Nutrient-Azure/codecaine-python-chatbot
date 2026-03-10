from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, chatbot, analysis

app = FastAPI(title="Codecaine Chatbot API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(chatbot.router)
app.include_router(analysis.router)

@app.get("/")
def root():
    return {"message": "Codecaine Chatbot API"}
