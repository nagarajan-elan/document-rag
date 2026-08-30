import uuid
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, timezone


class DocumentCreatePayload(BaseModel):
    status: Literal["uploaded", "chunking", "embedding", "ready", "error"] = "uploaded"
    filename: str
    object_key: str
    active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DocumentPatchPayload(BaseModel):
    status: Literal["uploaded", "chunking", "embedding", "ready", "error"] | None = None
    active: bool | None = None


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    status: str
    filename: str
    object_key: str
    active: bool
    created_at: datetime
