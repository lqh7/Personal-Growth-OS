"""
LLM Factory - Embeddings generation using sentence-transformers.
Supports Agno framework for AI agents.
"""
from typing import List, Optional
from functools import lru_cache

from .config import settings


class EmbeddingService:
    """Service for generating text embeddings using sentence-transformers."""

    def __init__(self, model_name: Optional[str] = None):
        """
        Initialize embedding service with specified model.

        Args:
            model_name: Model name for sentence-transformers.
                       If None, uses settings.EMBEDDING_MODEL
        """
        self.model_name = model_name or settings.EMBEDDING_MODEL
        self._model = None

    @property
    def model(self):
        """Lazy load the model to avoid startup overhead."""
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def embed_query(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Input text to embed

        Returns:
            List of floats representing the embedding vector
        """
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of input texts to embed

        Returns:
            List of embedding vectors
        """
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()

    @property
    def dimension(self) -> int:
        """Get the embedding dimension for the current model."""
        # all-MiniLM-L6-v2 produces 384-dimensional embeddings
        return 384


@lru_cache()
def get_embeddings() -> EmbeddingService:
    """Get cached embeddings service instance."""
    return EmbeddingService()


def get_chat_model_config() -> dict:
    """
    Get chat model configuration dictionary for Agno framework.

    Returns:
        dict: Configuration dictionary with model, api_key, and optional base_url
    """
    provider = settings.LLM_PROVIDER

    if provider == "openai":
        config = {
            "model": settings.OPENAI_MODEL,
            "api_key": settings.OPENAI_API_KEY,
        }
        if settings.OPENAI_API_BASE:
            config["base_url"] = settings.OPENAI_API_BASE
        return config

    elif provider == "claude":
        config = {
            "model": settings.ANTHROPIC_MODEL,
            "api_key": settings.ANTHROPIC_API_KEY,
        }
        if settings.ANTHROPIC_API_BASE:
            config["base_url"] = settings.ANTHROPIC_API_BASE
        return config

    elif provider == "ollama":
        return {
            "model": settings.OLLAMA_MODEL,
            "base_url": settings.OLLAMA_BASE_URL,
        }

    else:
        # Default to OpenAI config
        return {
            "model": settings.OPENAI_MODEL,
            "api_key": settings.OPENAI_API_KEY,
        }
