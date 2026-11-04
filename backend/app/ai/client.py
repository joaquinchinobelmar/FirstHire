"""Thin wrapper around the Anthropic SDK: one structured call, safe fallbacks.

Any failure (no key, network, refusal, invalid output) raises AIUnavailable so the
caller can switch to the deterministic offline engine. The demo never breaks.
"""

import logging
from typing import TypeVar

import anthropic
from pydantic import BaseModel

from ..config import settings

log = logging.getLogger("firsthire.ai")
T = TypeVar("T", bound=BaseModel)

# Models that accept server-side refusal fallbacks (`fallbacks: "default"`)
_FALLBACK_MODELS = {"claude-opus-5-5", "claude-opus-5", "claude-fable-5-1", "claude-sonnet-5-5"}
_FALLBACK_BETA = "server-side-fallback-2026-07-01"

_client: anthropic.Anthropic | None = None


class AIUnavailable(Exception):
    pass


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(timeout=90.0, max_retries=2)
    return _client


def structured_call(system: str, user: str, schema: type[T], max_tokens: int = 16000) -> T:
    if not settings.ai_enabled:
        raise AIUnavailable("AI is in offline mode")

    client = _get_client()
    common = dict(
        model=settings.claude_model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
        output_format=schema,
        output_config={"effort": settings.claude_effort},
    )
    try:
        if settings.claude_model in _FALLBACK_MODELS:
            try:
                resp = client.beta.messages.parse(**common, betas=[_FALLBACK_BETA], fallbacks="default")
            except anthropic.BadRequestError as e:
                log.warning("Fallback-enabled request rejected (%s); retrying without fallbacks", e.message)
                resp = client.messages.parse(**common)
        else:
            resp = client.messages.parse(**common)
    except anthropic.AuthenticationError as e:
        raise AIUnavailable("Invalid Anthropic credentials") from e
    except anthropic.RateLimitError as e:
        raise AIUnavailable("Rate limited") from e
    except anthropic.APIStatusError as e:
        raise AIUnavailable(f"API error {e.status_code}") from e
    except anthropic.APIConnectionError as e:
        raise AIUnavailable("Network error") from e
    except Exception as e:  # validation errors, unexpected SDK issues
        raise AIUnavailable(f"Unexpected AI error: {e}") from e

    if resp.stop_reason == "refusal":
        raise AIUnavailable("Model declined the request")
    if resp.stop_reason == "max_tokens":
        raise AIUnavailable("Response truncated")
    parsed = getattr(resp, "parsed_output", None)
    if parsed is None:
        raise AIUnavailable("No structured output returned")
    return parsed
