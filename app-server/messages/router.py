import uuid
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from .services import MessageService, get_message_service
from .schemas import MessagePayload, MessageResponse

router = APIRouter(tags=["Messages"])


@router.get("/", response_model=list[MessageResponse])
def get_messages(
    chat_id: uuid.UUID,
    page: int = 1,
    page_size: int = 10,
    service: MessageService = Depends(get_message_service),
):
    return service.get_messages(chat_id=chat_id, page=page, page_size=page_size)


@router.post("/")
async def create_message(
    chat_id: uuid.UUID,
    data: MessagePayload,
    service: MessageService = Depends(get_message_service),
):
    try:
        return StreamingResponse(
            service.generate_response(
                chat_id=chat_id,
                message=data.message,
            ),
            media_type="text/event-stream",
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
