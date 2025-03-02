"""Anthropic provider implementation."""

import os
from typing import Dict, Any, Optional, Iterator, List

from . import ANTHROPIC_AVAILABLE

if ANTHROPIC_AVAILABLE:
    from anthropic import Anthropic

from .base import LLMProvider
from rich.console import Console

console = Console()


class AnthropicProvider(LLMProvider):
    """Anthropic API provider."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the Anthropic provider."""
        self.config = config
        self.model = config.get("model", "claude-3-opus-20240229")
        self.api_key = config.get("api-key")
        self.client = None

        if ANTHROPIC_AVAILABLE and self.api_key:
            try:
                self.client = Anthropic(api_key=self.api_key)
            except Exception as e:
                console.print(
                    f"[red]Error initializing Anthropic client:[/red] {str(e)}"
                )

    def validate_config(self) -> bool:
        """Validate the provider configuration."""
        if not ANTHROPIC_AVAILABLE:
            console.print(
                "[red]Error:[/red] Anthropic Python package not installed. "
                "Install it with: [bold]pip install anthropic[/bold]"
            )
            return False

        if not self.api_key:
            console.print(
                "[red]Error:[/red] No API key provided for Anthropic. "
                "Set the ANTHROPIC_API_KEY environment variable or provide it in the .context file."
            )
            return False

        if not self.model:
            console.print(
                "[red]Error:[/red] No model specified for Anthropic. "
                "Please specify a model in the .context file."
            )
            return False

        if not self.client:
            return False

        return True

    def get_completion(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Get a completion from Anthropic."""
        if not self.validate_config():
            return "Error: Anthropic provider not properly configured."

        try:
            # Create the request parameters
            params = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
                "max_tokens": (max_tokens if max_tokens is not None else 1024),
            }

            if system_prompt:
                params["system"] = system_prompt

            response = self.client.messages.create(**params)

            if response.content and len(response.content) > 0:
                return response.content[0].text
            return ""

        except Exception as e:
            console.print(
                f"[red]Error getting completion from Anthropic:[/red] {str(e)}"
            )
            return f"Error: {str(e)}"

    def get_completion_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> Iterator[str]:
        """Stream a completion from Anthropic."""
        if not self.validate_config():
            yield "Error: Anthropic provider not properly configured."
            return

        try:
            params = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
                "max_tokens": (max_tokens if max_tokens is not None else 1024),
            }

            if system_prompt:
                params["system"] = system_prompt

            with self.client.messages.stream(**params) as stream:
                for text in stream.text_stream:
                    yield text

        except Exception as e:
            console.print(
                f"[red]Error streaming completion from Anthropic:[/red] {str(e)}"
            )
            yield f"Error: {str(e)}"
