import uuid

from fastapi import APIRouter, Depends

from .repository import (
    DocumentChunkRepository,
    get_document_chunk_repository,
)
from .schemas import DocumentChunkResponse

router = APIRouter(
    prefix="/documents/{document_id}/chunks",
    tags=["Document Chunks"],
)


@router.get("/", response_model=list[DocumentChunkResponse])
def get_document_chunks(
    document_id: uuid.UUID,
    page: int = 1,
    page_size: int = 10,
    repository: DocumentChunkRepository = Depends(get_document_chunk_repository),
):
    return repository.get_all(
        document_id=document_id,
        page=page,
        page_size=page_size,
    )
