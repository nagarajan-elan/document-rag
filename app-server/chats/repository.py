from datetime import datetime, timezone
import uuid
from .schemas import ChatCreatePayload, ChatPatchPayload
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from db.session import get_db
from .models import Chat


class ChatRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, chat_id: uuid.UUID):
        return self.db.get(Chat, chat_id)

    def get_all(self, page: int = 1, page_size: int = 10):
        offset = (page - 1) * page_size
        return self.db.scalars(
            select(Chat)
            .offset(offset)
            .limit(page_size)
            .order_by(Chat.updated_at.desc())
        ).all()

    def create(self, data: ChatCreatePayload):
        chat = Chat(**data.model_dump())

        self.db.add(chat)
        self.db.commit()
        self.db.refresh(chat)

        return chat

    def update(self, chat: Chat, data: ChatPatchPayload):
        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(chat, field, value)

        chat.updated_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(chat)

        return chat

    def delete(self, chat: Chat):
        self.db.delete(chat)
        self.db.commit()


def get_chat_repository(db: Session = Depends(get_db)):
    return ChatRepository(db)
