"""Shared Langfuse + Anthropic tracing setup.

Import `init_observability` and `observe` from here instead of configuring
Langfuse in every module.
"""

from functools import lru_cache

from langfuse import Langfuse, observe
from opentelemetry.instrumentation.anthropic import AnthropicInstrumentor

from policypal.config import get_settings

__all__ = ["init_observability", "observe"]


@lru_cache
def init_observability() -> Langfuse:
    """Create the Langfuse client and instrument Anthropic calls (runs once)."""
    settings = get_settings()
    client = Langfuse(
        public_key=settings.langfuse_public_key.get_secret_value(),
        secret_key=settings.langfuse_secret_key.get_secret_value(),
        base_url=settings.langfuse_base_url,
    )
    AnthropicInstrumentor().instrument()
    return client
