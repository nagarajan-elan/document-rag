from fastapi import APIRouter
from messages.router import router as messages_router

router = APIRouter(prefix="/chats", tags=["Chats"])


@router.get("/")
def get_chats():
    return []


@router.post("/")
def create_chat():
    return {"message": "Chat created successfully!"}


@router.get("/{chat_id}")
def get_chat(chat_id: str):
    return {"chat_id": chat_id, "message": "Chat details"}


@router.patch("/{chat_id}")
def update_chat(chat_id: str):
    return {"chat_id": chat_id, "message": "Chat updated successfully!"}


@router.delete("/{chat_id}")
def delete_chat(chat_id: str):
    return {"chat_id": chat_id, "message": "Chat deleted successfully!"}


router.include_router(messages_router, prefix="/{chat_id}/messages")
