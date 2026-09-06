import uuid

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from db.session import get_db
from .models import DocumentChunk


class DocumentChunkRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_all(self, document_id: uuid.UUID, page: int = 1, page_size: int = 10):
        offset = (page - 1) * page_size
        return self.db.scalars(
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document_id)
            .offset(offset)
            .limit(page_size)
            .order_by(DocumentChunk.chunk_index.asc())
        ).all()


def get_document_chunk_repository(db: Session = Depends(get_db)):
    return DocumentChunkRepository(db)
