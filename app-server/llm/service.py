from sentence_transformers import SentenceTransformer
from fastapi import Depends


embedding_model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2",
    device="cpu",
)


class LLMService:
    def __init__(self):
        pass

    def generate_embedding(self, content: str) -> list[float]:
        embeddings = embedding_model.encode(
            content,
            normalize_embeddings=True,
        )
        return embeddings.tolist()

    async def generate_response(self, msg: str):
        # Placeholder for streaming response logic
        pass


def get_llm_service():
    return LLMService()
