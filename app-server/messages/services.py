import uuid
import logging
from messages.schemas import MessageCreatePayload
from llm.service import LLMService, get_llm_service
from llm.constants import RAG_SYSTEM_PROMPT
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

    def get_augmented_messages(
        self,
        chat_id: uuid.UUID,
        user_message: str,
    ):
        # Generate embedding for user message
        user_message_embedding = self.llm_service.generate_embedding(user_message)

        # Fetch relevant chunks from DB
        document_chunks = self.document_chunk_repository.get_relevant_chunks(
            query_embedding=user_message_embedding, top_k=5
        )
        context_parts = []
        for i, chunk in enumerate(document_chunks, start=1):
            source = chunk.headers or ""
            context_parts.append(f"[Chunk {i} :: {source}]\n{chunk.content}")

        context_text = "\n\n---\n\n".join(context_parts)

        # Fetch previous messages for context
        previous_messages = self.get_messages(
            chat_id=chat_id,
            limit=6,
        )

        # Build RAG input
        input_messages = [{"role": "system", "content": RAG_SYSTEM_PROMPT}]
        for msg in previous_messages:
            input_messages.append({"role": msg.role, "content": msg.content})

        # Add the user message at the end
        input_messages.append(
            {
                "role": "user",
                "content": (
                    "Document context:\n\n"
                    f"{context_text}\n\n"
                    f"Question: {user_message}"
                ),
            }
        )
        return input_messages

    async def generate_response(self, chat_id: uuid.UUID, message: str):
        # User message record entry
        user_message = MessageCreatePayload(content=message, role="user")
        self.message_repository.create(chat_id, user_message)

        llm_message = []
        messages = self.get_augmented_messages(chat_id=chat_id, user_message=message)
        # messages = [{"role": "user", "content": message}]
        llm_response = await self.llm_service.generate_response(messages)
        async for chunk in llm_response:
            if chunk.choices:
                msg_in_chunk = chunk.choices[0].delta.content
                if msg_in_chunk:
                    yield msg_in_chunk
                    llm_message.append(msg_in_chunk)
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
