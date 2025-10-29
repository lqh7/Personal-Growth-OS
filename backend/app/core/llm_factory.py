"""
LLM Factory for creating LLM instances based on configuration.
Supports multiple providers: OpenAI, Claude (Anthropic), Ollama.
"""
from typing import Optional
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_anthropic import ChatAnthropic
from langchain_community.chat_models import ChatOllama
from langchain_community.embeddings import OllamaEmbeddings
from langchain.schema.language_model import BaseLanguageModel
from langchain.schema.embeddings import Embeddings

from .config import settings


class LLMFactory:
    """Factory class for creating LLM instances."""

    @staticmethod
    def create_chat_model(
        provider: Optional[str] = None,
        temperature: float = 0.7,
        **kwargs
    ) -> BaseLanguageModel:
        """
        Create a chat model instance based on the provider.

        Args:
            provider: LLM provider ('openai', 'claude', 'ollama').
                     If None, uses settings.LLM_PROVIDER
            temperature: Temperature for generation (0-1)
            **kwargs: Additional provider-specific arguments

        Returns:
            BaseLanguageModel: Configured chat model instance

        Raises:
            ValueError: If provider is not supported
        """
        provider = provider or settings.LLM_PROVIDER

        if provider == "openai":
            openai_kwargs = {
                "api_key": settings.OPENAI_API_KEY,
                "model": settings.OPENAI_MODEL,
                "temperature": temperature,
            }
            # Add custom base URL if provided
            if settings.OPENAI_API_BASE:
                openai_kwargs["base_url"] = settings.OPENAI_API_BASE
            openai_kwargs.update(kwargs)
            return ChatOpenAI(**openai_kwargs)

        elif provider == "claude":
            anthropic_kwargs = {
                "api_key": settings.ANTHROPIC_API_KEY,
                "model": settings.ANTHROPIC_MODEL,
                "temperature": temperature,
            }
            # Add custom base URL if provided
            if settings.ANTHROPIC_API_BASE:
                anthropic_kwargs["base_url"] = settings.ANTHROPIC_API_BASE
            anthropic_kwargs.update(kwargs)
            return ChatAnthropic(**anthropic_kwargs)

        elif provider == "ollama":
            return ChatOllama(
                base_url=settings.OLLAMA_BASE_URL,
                model=settings.OLLAMA_MODEL,
                temperature=temperature,
                **kwargs
            )

        else:
            raise ValueError(
                f"Unsupported LLM provider: {provider}. "
                f"Supported providers: openai, claude, ollama"
            )

    @staticmethod
    def create_embeddings(
        provider: Optional[str] = None,
        **kwargs
    ) -> Embeddings:
        """
        Create an embeddings instance.

        Args:
            provider: Embeddings provider. If None, uses settings.LLM_PROVIDER
            **kwargs: Additional provider-specific arguments

        Returns:
            Embeddings: Configured embeddings instance
        """
        provider = provider or settings.LLM_PROVIDER

        # For embeddings, we prefer OpenAI or sentence-transformers
        # Ollama can also be used for local embeddings
        if provider in ["openai", "claude"]:
            return OpenAIEmbeddings(
                api_key=settings.OPENAI_API_KEY,
                model=settings.EMBEDDING_MODEL,
                **kwargs
            )

        elif provider == "ollama":
            return OllamaEmbeddings(
                base_url=settings.OLLAMA_BASE_URL,
                model=settings.OLLAMA_MODEL,
                **kwargs
            )

        else:
            # Default to sentence-transformers for local embeddings
            from langchain_community.embeddings import HuggingFaceEmbeddings
            return HuggingFaceEmbeddings(
                model_name=settings.EMBEDDING_MODEL,
                **kwargs
            )


# Convenience functions for common use cases
def get_chat_model(temperature: float = 0.7, **kwargs) -> BaseLanguageModel:
    """Get the default chat model configured in settings."""
    return LLMFactory.create_chat_model(temperature=temperature, **kwargs)


def get_embeddings(**kwargs) -> Embeddings:
    """Get the default embeddings model configured in settings."""
    return LLMFactory.create_embeddings(**kwargs)
