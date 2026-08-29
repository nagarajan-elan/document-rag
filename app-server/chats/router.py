from typing import List
import uuid
from .schemas import ChatCreatePayload, ChatPatchPayload, ChatResponse
from fastapi import APIRouter, Depends
from messages.router import router as messages_router
from .repository import ChatRepository, get_chat_repository

router = APIRouter(prefix="/chats", tags=["Chats"])


@router.get("/", response_model=List[ChatResponse])
def get_chats(
    page: int = 1,
    page_size: int = 10,
    archived: bool = False,
    respository: ChatRepository = Depends(get_chat_repository),
):
    return respository.get_all(page=page, page_size=page_size, archived=archived)


@router.post("/", response_model=ChatResponse)
def create_chat(
    payload: ChatCreatePayload,
    respository: ChatRepository = Depends(get_chat_repository),
):
    chat = respository.create(data=payload)
    return chat


@router.get("/{chat_id}", response_model=ChatResponse)
def get_chat(
    chat_id: uuid.UUID,
    respository: ChatRepository = Depends(get_chat_repository),
):
    chat = respository.get_by_id(chat_id)
    if not chat:
        return {"chat_id": chat_id, "message": "Chat not found!"}
    return chat


@router.patch("/{chat_id}", response_model=ChatResponse)
def patch_chat(
    chat_id: uuid.UUID,
    payload: ChatPatchPayload,
    respository: ChatRepository = Depends(get_chat_repository),
):
    chat = respository.get_by_id(chat_id)
    if not chat:
        return {"chat_id": chat_id, "message": "Chat not found!"}

    return respository.update(chat=chat, data=payload)


@router.delete("/{chat_id}")
def delete_chat(
    chat_id: uuid.UUID, respository: ChatRepository = Depends(get_chat_repository)
):
    chat = respository.get_by_id(chat_id)
    if not chat:
        return {"chat_id": chat_id, "message": "Chat not found!"}

    respository.delete(chat)
    return {"chat_id": chat_id, "message": "Chat deleted successfully!"}


router.include_router(messages_router, prefix="/{chat_id}/messages")
