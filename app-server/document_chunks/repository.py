import time
import uuid

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from db.session import get_db
from metrics import DOCUMENT_CHUNK_FETCH_DURATION
from .models import DocumentChunk


class DocumentChunkRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_all(self, document_id: uuid.UUID, page: int = 1, page_size: int = 10):
        start = time.perf_counter()
        offset = (page - 1) * page_size
        try:
            return self.db.scalars(
                select(DocumentChunk)
                .where(DocumentChunk.document_id == document_id)
                .offset(offset)
                .limit(page_size)
                .order_by(DocumentChunk.chunk_index.asc())
            ).all()
        finally:
            DOCUMENT_CHUNK_FETCH_DURATION.labels(operation="list").observe(
                time.perf_counter() - start
            )

    def get_relevant_chunks(self, query_embedding: list[float], top_k: int = 4):
        start = time.perf_counter()
        distance = DocumentChunk.embedding.cosine_distance(query_embedding)
        try:
            return self.db.scalars(
                select(
                    DocumentChunk,
                    distance.label("distance"),
                )
                .where(DocumentChunk.embedding.is_not(None))
                .order_by(distance)
                .limit(top_k)
            ).all()
        finally:
            DOCUMENT_CHUNK_FETCH_DURATION.labels(operation="relevant").observe(
                time.perf_counter() - start
            )


def get_document_chunk_repository(db: Session = Depends(get_db)):
    return DocumentChunkRepository(db)
