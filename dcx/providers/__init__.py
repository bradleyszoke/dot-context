"""Providers for different LLM services."""

from typing import Dict, Any, Optional
from rich.console import Console

# Import availability flags at the module level so they can be patched in tests
try:
    import openai

    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import anthropic

    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

from .base import LLMProvider
from .openai import OpenAIProvider
from .anthropic import AnthropicProvider
from .gemini import GeminiProvider

console = Console()


def get_provider(name: str, config: Dict[str, Any]) -> Optional[LLMProvider]:
    """
    Get a provider instance based on the provider name.

    Args:
        name: Provider name from config (e.g., 'openai', 'anthropic', 'gemini')
        config: Provider configuration dictionary

    Returns:
        A provider instance or None if provider is not supported
    """
    provider_name = config.get("provider", "").lower()

    if provider_name == "openai":
        if not OPENAI_AVAILABLE:
            console.print(
                "[yellow]Warning:[/yellow] OpenAI provider requested but the openai "
                "package is not installed. Install it with: [bold]pip install dot-context[openai][/bold]"
            )
            return None
        return OpenAIProvider(config)

    elif provider_name == "anthropic":
        if not ANTHROPIC_AVAILABLE:
            console.print(
                "[yellow]Warning:[/yellow] Anthropic provider requested but the anthropic "
                "package is not installed. Install it with: [bold]pip install dot-context[anthropic][/bold]"
            )
            return None
        return AnthropicProvider(config)

    elif provider_name == "gemini":
        if not OPENAI_AVAILABLE:
            console.print(
                "[yellow]Warning:[/yellow] Gemini provider requested but the openai "
                "package is not installed. Install it with: [bold]pip install dot-context[openai][/bold]"
            )
            return None
        return GeminiProvider(config)

    console.print(f"[red]Error:[/red] Unsupported provider: {provider_name}")
    return None
