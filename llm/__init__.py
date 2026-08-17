"""Provider-agnostic LLM access (Anthropic / OpenAI / Gemini) with a fully
offline fallback path used throughout ``analytics.insights`` and ``chat.nlq``.
"""
from .client import LLMUnavailableError, active_provider_name, generate, is_available

__all__ = ["LLMUnavailableError", "active_provider_name", "generate", "is_available"]
