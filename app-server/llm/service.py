import os
from sentence_transformers import SentenceTransformer
from openai import AsyncOpenAI

from config import settings


class LLMService:
    def __init__(self):
        self.embedding_model = SentenceTransformer(
            "sentence-transformers/all-MiniLM-L6-v2",
            device="cpu",
        )

        self.client = AsyncOpenAI(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL,
        )

        self.chat_model = settings.CHAT_MODEL

    def generate_embedding(self, content: str) -> list[float]:
        embeddings = self.embedding_model.encode(
            content,
            normalize_embeddings=True,
        )
        return embeddings.tolist()

    async def generate_response(self, messages):
        return await self.client.chat.completions.create(
            model=self.chat_model,
            messages=messages,
            stream=True,
        )


llm_service = LLMService()


def get_llm_service() -> LLMService:
    return llm_service
