import uuid_utils as uuid
from sqlalchemy import Uuid, DateTime
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column

from db.base import Base


class Chat(Base):
    __tablename__ = "chats"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid7
    )
    name: Mapped[str]
    archived: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
