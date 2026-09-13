import uuid

from fastapi import APIRouter, Depends

from .repository import (
    DocumentChunkRepository,
    get_document_chunk_repository,
)
from .schemas import DocumentChunkResponse
from llm.service import get_llm_service

router = APIRouter(
    prefix="/documents-chunks",
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


@router.get("/relevant", response_model=list[DocumentChunkResponse])
def get_relevant_chunks(
    query: str,
    top_k: int = 5,
    repository: DocumentChunkRepository = Depends(get_document_chunk_repository),
):
    llm_service = get_llm_service()
    user_message_embedding = llm_service.generate_embedding(query)
    # Fetch relevant chunks from DB
    document_chunks = repository.get_relevant_chunks(
        query_embedding=user_message_embedding, top_k=top_k
    )
    return document_chunks
