"""AI assistance layer.

Talks to our endpoint (``https://llm-router.iam.hpc.fau.edu/v1``) using the
OpenAI Python client, with the default model ``ornith-1.5`` and a fast model
``ornith-1.5:9b``. The context window is 100k tokens; when the assembled
context exceeds the reserve we compress it (see :func:`compress_context`).
"""
from __future__ import annotations

from functools import lru_cache

from openai import OpenAI

from .config import get_settings


@lru_cache
def get_client() -> OpenAI:
    settings = get_settings()
    return OpenAI(base_url=settings.ai_base_url, api_key=settings.ai_api_key or "not-needed")


def _tokens_for(text: str) -> int:
    """Rough token estimate (no hard dependency on tiktoken being installed)."""
    try:
        import tiktoken

        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except Exception:
        # ~4 chars per English token fallback.
        return max(1, len(text) // 4)


def compress_context(text: str, max_tokens: int | None = None) -> str:
    """Compress ``text`` to fit within ``max_tokens`` if it is too large.

    Uses the fast model to summarise the overflow. When the text already fits,
    it is returned unchanged.
    """
    settings = get_settings()
    limit = max_tokens or (settings.ai_context_tokens - settings.ai_reserve_tokens)
    if _tokens_for(text) <= limit:
        return text

    client = get_client()
    prompt = (
        "You are compressing a story-development document. Keep every named "
        "character, place, theme, arc and plot beat, and all numeric/order "
        "information, but remove repetition and filler. Return the condensed "
        "version in the same markdown structure.\n\n"
        f"DOCUMENT:\n{text}"
    )
    try:
        resp = client.chat.completions.create(
            model=settings.ai_fast_model,
            messages=[
                {"role": "system", "content": "You compress writing faithfully."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=settings.ai_context_tokens - limit,
        )
        return resp.choices[0].message.content or text
    except Exception:
        # Never block the author: fall back to naive truncation.
        return text[-limit:]


def complete(
    system: str,
    user: str,
    *,
    fast: bool = False,
    max_tokens: int = 4000,
    temperature: float = 0.8,
) -> str:
    """Run a chat completion and return the text (empty string on failure)."""
    settings = get_settings()
    client = get_client()
    try:
        resp = client.chat.completions.create(
            model=settings.ai_fast_model if fast else settings.ai_model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return resp.choices[0].message.content or ""
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# Prompt helpers for the author workflow
# ---------------------------------------------------------------------------
def prompt_for(kind: str, author_input: str, context: str = "") -> tuple[str, str]:
    """Return a (system, user) prompt pair for a generation ``kind``."""
    system = "You are a professional book editor and writing partner."
    ctx = f"\n\nRelevant context:\n{context}" if context else ""
    user = (
        f"Help the author develop their {kind}.{ctx}\n\n"
        f"Author input:\n{author_input}\n\n"
        "Respond in well-structured markdown. Do not invent facts the author "
        "has not provided; offer options where the input is open-ended."
    )
    return system, user
