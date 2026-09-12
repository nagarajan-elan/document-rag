import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from .services import MessageService, get_message_service
from .schemas import MessagePayload, MessageResponse

router = APIRouter(tags=["Messages"])


@router.get("/", response_model=list[MessageResponse])
def get_messages(
    chat_id: uuid.UUID,
    before: str | None = Query(default=None),
    limit: int = Query(default=10, ge=1, le=100),
    service: MessageService = Depends(get_message_service),
):
    return service.get_messages(
        chat_id=chat_id,
        before=before,
        limit=limit,
    )


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
