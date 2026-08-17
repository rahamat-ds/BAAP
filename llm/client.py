"""Provider-agnostic LLM client.

Supports Anthropic, OpenAI and Google Gemini via optional SDKs, auto-
selecting whichever provider has a configured API key (or an explicit
choice from Settings). The rest of the platform never talks to a provider
SDK directly — it calls :func:`generate` and always gets a string back,
even with zero API keys configured (an ``LLMUnavailableError`` signals
callers to fall back to the deterministic, rule-based engines used
throughout ``analytics.insights`` and ``chat.nlq``).
"""
from __future__ import annotations

from dataclasses import dataclass

from config import settings
from core.logging_config import get_logger

logger = get_logger(__name__)


class LLMUnavailableError(RuntimeError):
    """Raised when no LLM provider is configured or a call fails."""


@dataclass(frozen=True)
class ProviderChoice:
    provider: str
    model: str


def _resolve_provider(explicit: str | None = None) -> ProviderChoice | None:
    choice = explicit or settings.default_llm_provider
    order = ["anthropic", "openai", "gemini"] if choice == "auto" else [choice]
    for name in order:
        key = {
            "anthropic": settings.anthropic_api_key,
            "openai": settings.openai_api_key,
            "gemini": settings.gemini_api_key,
        }.get(name)
        if key:
            from config import LLM_MODELS

            return ProviderChoice(name, LLM_MODELS.get(name, [""])[0])
    return None


def is_available() -> bool:
    return _resolve_provider() is not None


def active_provider_name() -> str | None:
    choice = _resolve_provider()
    return choice.provider if choice else None


def generate(prompt: str, system: str = "", temperature: float = 0.4, max_tokens: int = 800) -> str:
    """Generate text from the active LLM provider.

    Raises :class:`LLMUnavailableError` if no provider is configured or the
    call fails — callers are expected to catch this and use a deterministic
    fallback rather than surface a raw exception to the user.
    """
    choice = _resolve_provider()
    if choice is None:
        raise LLMUnavailableError("No LLM provider configured. Add an API key in Settings.")

    try:
        if choice.provider == "anthropic":
            return _call_anthropic(prompt, system, temperature, max_tokens, choice.model)
        if choice.provider == "openai":
            return _call_openai(prompt, system, temperature, max_tokens, choice.model)
        if choice.provider == "gemini":
            return _call_gemini(prompt, system, temperature, max_tokens, choice.model)
    except LLMUnavailableError:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.warning("LLM call failed (%s): %s", choice.provider, exc)
        raise LLMUnavailableError(str(exc)) from exc

    raise LLMUnavailableError(f"Unknown provider: {choice.provider}")


def _call_anthropic(prompt: str, system: str, temperature: float, max_tokens: int, model: str) -> str:
    try:
        import anthropic
    except ImportError as exc:
        raise LLMUnavailableError("The 'anthropic' package is not installed.") from exc

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    response = client.messages.create(
        model=model, max_tokens=max_tokens, temperature=temperature,
        system=system or "You are a helpful business data analyst.",
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(block.text for block in response.content if getattr(block, "type", "") == "text").strip()


def _call_openai(prompt: str, system: str, temperature: float, max_tokens: int, model: str) -> str:
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise LLMUnavailableError("The 'openai' package is not installed.") from exc

    client = OpenAI(api_key=settings.openai_api_key)
    response = client.chat.completions.create(
        model=model, temperature=temperature, max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": system or "You are a helpful business data analyst."},
            {"role": "user", "content": prompt},
        ],
    )
    return (response.choices[0].message.content or "").strip()


def _call_gemini(prompt: str, system: str, temperature: float, max_tokens: int, model: str) -> str:
    try:
        import google.generativeai as genai
    except ImportError as exc:
        raise LLMUnavailableError("The 'google-generativeai' package is not installed.") from exc

    genai.configure(api_key=settings.gemini_api_key)
    client = genai.GenerativeModel(model, system_instruction=system or None)
    response = client.generate_content(
        prompt,
        generation_config={"temperature": temperature, "max_output_tokens": max_tokens},
    )
    return (response.text or "").strip()
