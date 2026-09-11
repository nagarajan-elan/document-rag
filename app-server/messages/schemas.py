import uuid
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, timezone


class MessageCreatePayload(BaseModel):
    content: str
    role: Literal["system", "user", "assistant"]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    content: str
    role: Literal["system", "user", "assistant"]
    chat_id: uuid.UUID
    created_at: datetime


class MessagePayload(BaseModel):
    message: str
