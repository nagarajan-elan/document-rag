import uuid
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, timezone


class ChatCreatePayload(BaseModel):
    name: str
    archived: bool | None = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ChatPatchPayload(BaseModel):
    name: str | None = None
    archived: bool | None = None
    created_at: datetime | None = None


class ChatResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    archived: bool
    created_at: datetime
    updated_at: datetime
