import time
import uuid
import logging
from opentelemetry import trace
from metrics import (
    CHAT_MESSAGES_FETCH_DURATION,
    LLM_INPUT_TOKENS,
    LLM_OUTPUT_TOKENS,
    LLM_STREAM_DURATION,
    LLM_TIME_TO_FIRST_TOKEN,
)
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
tracer = trace.get_tracer(__name__)


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
        start = time.perf_counter()
        try:
            return self.message_repository.get_all(
                chat_id=chat_id,
                before=before,
                limit=limit,
            )
        finally:
            CHAT_MESSAGES_FETCH_DURATION.labels(operation="recent").observe(
                time.perf_counter() - start
            )

    def get_augmented_messages(
        self,
        chat_id: uuid.UUID,
        user_message: str,
    ):
        # Generate embedding for user message
        with tracer.start_as_current_span("user_message_embedding"):
            user_message_embedding = self.llm_service.generate_embedding(user_message)

        # Fetch relevant chunks from DB
        with tracer.start_as_current_span("relevant_chunk_fetch"):
            document_chunks = self.document_chunk_repository.get_relevant_chunks(
                query_embedding=user_message_embedding, top_k=5
            )
        context_parts = []
        for i, chunk in enumerate(document_chunks, start=1):
            source = chunk.headers or ""
            context_parts.append(f"[Chunk {i} :: {source}]\n{chunk.content}")

        context_text = "\n\n---\n\n".join(context_parts)

        # Fetch previous messages for context
        with tracer.start_as_current_span("previous_msgs_fetch"):
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
        with tracer.start_as_current_span("user_message_persist"):
            user_message = MessageCreatePayload(content=message, role="user")
            self.message_repository.create(chat_id, user_message)

        llm_message = []
        with tracer.start_as_current_span("augment_messages"):
            messages = self.get_augmented_messages(
                chat_id=chat_id,
                user_message=message,
            )
        # messages = [{"role": "user", "content": message}]
        with tracer.start_as_current_span("llm") as llm_span:
            stream_start = time.perf_counter()
            first_token_recorded = False
            try:
                with tracer.start_as_current_span("llm_request"):
                    llm_response = await self.llm_service.generate_response(messages)
                async for chunk in llm_response:
                    if chunk.usage:
                        model = chunk.model or self.llm_service.chat_model
                        LLM_INPUT_TOKENS.labels(model=model).inc(
                            chunk.usage.prompt_tokens
                        )
                        LLM_OUTPUT_TOKENS.labels(model=model).inc(
                            chunk.usage.completion_tokens
                        )
                    if chunk.choices:
                        msg_in_chunk = chunk.choices[0].delta.content
                        if msg_in_chunk:
                            if not first_token_recorded:
                                LLM_TIME_TO_FIRST_TOKEN.observe(
                                    time.perf_counter() - stream_start
                                )
                                first_token_recorded = True
                                llm_span.add_event("first_token")
                            llm_message.append(msg_in_chunk)
                            yield msg_in_chunk
            finally:
                LLM_STREAM_DURATION.observe(time.perf_counter() - stream_start)
        with tracer.start_as_current_span("assistant_message_persist"):
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
