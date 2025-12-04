"""
LLM utility functions for authentication handling.

Provides helper functions to create LLM instances with proper authentication,
supporting both standard API keys and JWT tokens for proxy services.
"""
from app.core.config import settings


def create_openai_chat_model(temperature: float = 0.7, streaming: bool = True):
    """
    Create ChatOpenAI instance with proper authentication.

    Automatically detects and handles:
    - Standard OpenAI API keys (sk-...)
    - JWT tokens for proxy services (eyJ...) - uses Authorization header

    Args:
        temperature: Model temperature (default: 0.7)
        streaming: Enable streaming responses (default: True)

    Returns:
        ChatOpenAI instance configured with proper authentication

    Example:
        >>> llm = create_openai_chat_model(temperature=0.5)
        >>> # Works with both:
        >>> # - OPENAI_API_KEY=sk-... (standard)
        >>> # - OPENAI_API_KEY=eyJ... (JWT for TrendMicro proxy)
    """
    from langchain_openai import ChatOpenAI

    # Detect JWT token (starts with "eyJ" - base64 encoded JSON)
    is_jwt = settings.OPENAI_API_KEY.startswith("eyJ")

    # LangChain's ChatOpenAI automatically supports both sync and async
    # For JWT tokens, we can pass them directly as api_key
    # The proxy will handle JWT authentication
    return ChatOpenAI(
        model=settings.OPENAI_MODEL,
        api_key=settings.OPENAI_API_KEY,  # Works with both sk-* and JWT tokens
        base_url=settings.OPENAI_API_BASE if settings.OPENAI_API_BASE else None,
        streaming=streaming,
        temperature=temperature,
    )


def get_langchain_llm_with_auth():
    """
    Get LangChain-compatible LLM instance with proper authentication.

    This is a compatibility wrapper for get_langchain_llm() that adds
    JWT authentication support.

    Supports multiple providers:
    - openai: ChatOpenAI (with JWT support)
    - claude: ChatAnthropic
    - ollama: ChatOllama

    Returns:
        LangChain ChatModel instance with streaming enabled

    Raises:
        ValueError: If provider is not supported
    """
    provider = settings.LLM_PROVIDER

    if provider == "openai":
        return create_openai_chat_model(
            temperature=getattr(settings, "TEMPERATURE", 0.7),
            streaming=True
        )

    elif provider == "claude":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model=settings.ANTHROPIC_MODEL,
            api_key=settings.ANTHROPIC_API_KEY,
            base_url=getattr(settings, "ANTHROPIC_API_BASE", None) if getattr(settings, "ANTHROPIC_API_BASE", None) else None,
            streaming=True,
            temperature=getattr(settings, "TEMPERATURE", 0.7),
        )

    elif provider == "ollama":
        from langchain_community.chat_models import ChatOllama
        return ChatOllama(
            model=settings.OLLAMA_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
            temperature=getattr(settings, "TEMPERATURE", 0.7),
        )

    else:
        raise ValueError(f"Unsupported LLM provider: {provider}. Supported: openai, claude, ollama")
