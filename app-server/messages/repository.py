import uuid
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

    def get_all(self, chat_id: uuid.UUID, page: int = 1, page_size: int = 10):
        offset = (page - 1) * page_size
        return self.db.scalars(
            select(Message)
            .offset(offset)
            .limit(page_size)
            .where(Message.chat_id == chat_id)
            .order_by(Message.created_at.asc())
        ).all()

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
