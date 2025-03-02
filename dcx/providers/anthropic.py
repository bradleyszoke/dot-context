"""Anthropic provider implementation."""

import os
from typing import Dict, Any, Optional, Iterator, List

# Use the module-level OPENAI_AVAILABLE from __init__.py
from . import ANTHROPIC_AVAILABLE

# Only import OpenAI if the package is available
if ANTHROPIC_AVAILABLE:
    from anthropic import Anthropic

from .base import LLMProvider
from rich.console import Console

console = Console()


class AnthropicProvider(LLMProvider):
    """Anthropic API provider."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Anthropic provider.

        Args:
            config: Provider configuration from the .context file
        """
        self.config = config
        self.model = config.get("model", "claude-3-opus-20240229")
        self.api_key = config.get("api-key")
        self.client = None

        # Initialize client if Anthropic is available
        if ANTHROPIC_AVAILABLE and self.api_key:
            try:
                self.client = Anthropic(api_key=self.api_key)
            except Exception as e:
                console.print(
                    f"[red]Error initializing Anthropic client:[/red] {str(e)}"
                )

    def validate_config(self) -> bool:
        """
        Validate that the provider has all required configuration.

        Returns:
            True if configuration is valid, False otherwise
        """
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
        """
        Get a completion from Anthropic.

        Args:
            prompt: The prompt to send to the model
            system_prompt: Optional system instructions
            temperature: Temperature parameter (0.0 to 1.0)
            max_tokens: Maximum tokens to generate (None for model default)

        Returns:
            The generated completion text
        """
        if not self.validate_config():
            return "Error: Anthropic provider not properly configured."

        messages = [{"role": "user", "content": prompt}]

        try:
            response = self.client.messages.create(
                model=self.model,
                messages=messages,
                system=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            # Extract text from the response
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
        """
        Stream a completion from Anthropic.

        Args:
            prompt: The prompt to send to the model
            system_prompt: Optional system instructions
            temperature: Temperature parameter (0.0 to 1.0)
            max_tokens: Maximum tokens to generate (None for model default)

        Returns:
            Iterator yielding completion text chunks
        """
        if not self.validate_config():
            yield "Error: Anthropic provider not properly configured."
            return

        messages = [{"role": "user", "content": prompt}]

        try:
            with self.client.messages.stream(
                model=self.model,
                messages=messages,
                system=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
            ) as stream:
                for text in stream.text_stream:
                    yield text

        except Exception as e:
            console.print(
                f"[red]Error streaming completion from Anthropic:[/red] {str(e)}"
            )
            yield f"Error: {str(e)}"
