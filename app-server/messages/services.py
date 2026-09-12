import uuid
import logging
from messages.schemas import MessageCreatePayload
from llm.service import LLMService, get_llm_service
from document_chunks.repository import (
    DocumentChunkRepository,
    get_document_chunk_repository,
)
from fastapi import Depends
from .repository import MessageRepository, get_message_repository

logger = logging.getLogger(__name__)


class MessageService:
    def __init__(
        self,
        message_repository: MessageRepository,
        document_chunk_repository: DocumentChunkRepository,
        llm_service: LLMService,
    ):
        self.message_repository = message_repository
        self.document_chunk_repository = document_chunk_repository
        self.llm_service = llm_service

    def get_messages(
        self,
        chat_id: uuid.UUID,
        before: str | None = None,
        limit: int = 10,
    ):
        return self.message_repository.get_all(
            chat_id=chat_id,
            before=before,
            limit=limit,
        )

    async def generate_response(self, chat_id: uuid.UUID, message: str):
        # User message record entry
        user_message = MessageCreatePayload(content=message, role="user")
        self.message_repository.create(chat_id, user_message)

        # Generate embedding for user message
        user_message_embedding = self.llm_service.generate_embedding(message)

        # Fetch relevant chunks from DB
        document_chunks = self.document_chunk_repository.get_relevant_chunks(
            query_embedding=user_message_embedding, top_k=4
        )
        # llm_response = self.llm_service.generate_response(message, document_chunks)
        llm_message = []
        for i in range(100):
            import asyncio

            await asyncio.sleep(0.1)
            yield f"{message}\n\n"
            llm_message.append(message)
        # TODO: Make LLM call and stream
        self.message_repository.create(
            chat_id,
            MessageCreatePayload(content="".join(llm_message), role="assistant"),
        )


def get_message_service(
    message_repository: MessageRepository = Depends(get_message_repository),
    document_chunk_repository: DocumentChunkRepository = Depends(
        get_document_chunk_repository
    ),
    llm_service: LLMService = Depends(get_llm_service),
):
    return MessageService(message_repository, document_chunk_repository, llm_service)
