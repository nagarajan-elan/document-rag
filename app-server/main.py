from fastapi import FastAPI
from chats.router import router as chats_router
from documents.router import router as documents_router
from db.models import Base

app = FastAPI()
app.include_router(chats_router)
app.include_router(documents_router)


@app.get("/")
def root():
    return {"message": "🐝 Welcome to Knowledge Base!! 🤩"}
