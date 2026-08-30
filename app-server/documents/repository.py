import uuid
from db.session import get_db
from .models import Document
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import Session
from .schemas import DocumentCreatePayload, DocumentPatchPayload


class DocumentRepository:

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, document_id: uuid.UUID):
        return self.db.get(Document, document_id)

    def get_all(self, page: int = 1, page_size: int = 10):
        offset = (page - 1) * page_size
        return self.db.scalars(
            select(Document)
            .offset(offset)
            .limit(page_size)
            .order_by(Document.created_at.desc())
        ).all()

    def create(self, data: DocumentCreatePayload):
        document = Document(**data.model_dump())
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        return document

    def update(self, document: Document, data: DocumentPatchPayload):
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(document, key, value)
        self.db.commit()
        self.db.refresh(document)
        return document


def get_document_repository(db: Session = Depends(get_db)):
    return DocumentRepository(db)
