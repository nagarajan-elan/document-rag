import uuid
from datetime import datetime, timezone

from .schemas import MessageCreatePayload
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from chats.models import Chat
from db.session import get_db
from .models import Message


class MessageRepository:

    def __init__(self, db: Session):
        self.db = db

    def _coerce_datetime(self, value):
        if value is None:
            return datetime.now(timezone.utc)

        if isinstance(value, datetime):
            return value

        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))

    def get_all(
        self,
        chat_id: uuid.UUID,
        before: datetime | str | None = None,
        limit: int = 10,
    ):
        if limit <= 0:
            limit = 10

        before_dt = self._coerce_datetime(before)
        query = select(Message).where(
            Message.chat_id == chat_id, Message.created_at < before_dt
        )

        rows = self.db.scalars(
            query.order_by(Message.created_at.desc()).limit(limit)
        ).all()

        return reversed(rows)

    def create(self, chat_id: uuid.UUID, data: MessageCreatePayload):
        chat = self.db.get(Chat, chat_id)
        if chat is None:
            raise ValueError(f"Chat with id {chat_id} does not exist.")

        message = Message(**data.model_dump(), chat_id=chat_id)

        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)

        return message


def get_message_repository(db: Session = Depends(get_db)):
    return MessageRepository(db)
