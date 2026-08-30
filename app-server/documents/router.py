import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from .repository import (
    DocumentRepository,
    get_document_repository,
)
from .schemas import DocumentPatchPayload, DocumentResponse, DocumentCreatePayload
from config import settings
from storage.minio import client as cloud_client

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.get("/", response_model=list[DocumentResponse])
def get_documents(
    page: int = 1,
    page_size: int = 10,
    repository: DocumentRepository = Depends(get_document_repository),
):
    return repository.get_all(page=page, page_size=page_size)


@router.post("/", response_model=DocumentResponse)
def upload_document(
    file: UploadFile = File(...),
    repository: DocumentRepository = Depends(get_document_repository),
):
    extension = Path(file.filename).suffix.lower()
    object_key = f"documents/{uuid.uuid4()}{extension}"
    try:
        cloud_client.put_object(
            bucket_name=settings.MINIO_BUCKET,
            object_name=object_key,
            data=file.file,
            length=-1,
            part_size=10 * 1024 * 1024,
            content_type=file.content_type or "application/octet-stream",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {e}")

    document = repository.create(
        data=DocumentCreatePayload(
            status="uploaded", filename=file.filename, object_key=object_key
        )
    )
    return document


@router.patch("/{document_id}", response_model=DocumentResponse)
def patch_document(
    document_id: uuid.UUID,
    payload: DocumentPatchPayload,
    repository: DocumentRepository = Depends(get_document_repository),
):
    document = repository.get_by_id(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return repository.update(document=document, data=payload)
