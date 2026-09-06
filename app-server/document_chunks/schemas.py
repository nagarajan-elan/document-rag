import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DocumentChunkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    document_id: uuid.UUID
    chunk_index: int
    status: str
    headers: str | None
    content: str
    page_start: int
    page_end: int
    created_at: datetime
