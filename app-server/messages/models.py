import uuid
from sqlalchemy import Uuid, DateTime, ForeignKey, Index
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    chat_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("chats.id", ondelete="CASCADE")
    )
    role: Mapped[str]
    content: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        Index(
            "ix_messages_chat_created_id",
            "chat_id",
            "created_at",
        ),
    )
