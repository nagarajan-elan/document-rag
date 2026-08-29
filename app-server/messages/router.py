import uuid
from fastapi import APIRouter, Depends, HTTPException

from .repository import MessageRepository, get_message_repository
from .schemas import MessageResponse, MessageCreatePayload

router = APIRouter(tags=["Messages"])


@router.get("/", response_model=list[MessageResponse])
def get_messages(
    chat_id: uuid.UUID,
    page: int = 1,
    page_size: int = 10,
    repository: MessageRepository = Depends(get_message_repository),
):
    return repository.get_all(chat_id=chat_id, page=page, page_size=page_size)


@router.post("/", response_model=MessageResponse)
def create_message(
    chat_id: uuid.UUID,
    payload: MessageCreatePayload,
    repository: MessageRepository = Depends(get_message_repository),
):
    try:
        return repository.create(chat_id=chat_id, data=payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
