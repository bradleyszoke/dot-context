"""Gemini provider implementation using OpenAI compatibility layer."""

import os
from typing import Dict, Any, Optional, Iterator, List

# We'll use the OpenAI client for Gemini through its compatibility mode
# Use the module-level OPENAI_AVAILABLE from __init__.py
from . import OPENAI_AVAILABLE

# Only import OpenAI if the package is available
if OPENAI_AVAILABLE:
    from openai import OpenAI

from .base import LLMProvider
from rich.console import Console

console = Console()

# Gemini API base URL for OpenAI compatibility
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"


class GeminiProvider(LLMProvider):
    """Gemini API provider using OpenAI compatibility."""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Gemini provider.

        Args:
            config: Provider configuration from the .context file
        """
        self.config = config
        self.model = config.get("model", "gemini-2.0-flash")
        self.api_key = config.get("api-key")
        self.client = None

        # Initialize client if OpenAI is available
        if OPENAI_AVAILABLE and self.api_key:
            try:
                self.client = OpenAI(api_key=self.api_key, base_url=GEMINI_BASE_URL)
            except Exception as e:
                console.print(f"[red]Error initializing Gemini client:[/red] {str(e)}")

    def validate_config(self) -> bool:
        """
        Validate that the provider has all required configuration.

        Returns:
            True if configuration is valid, False otherwise
        """
        if not OPENAI_AVAILABLE:
            console.print(
                "[red]Error:[/red] OpenAI Python package not installed. "
                "Install it with: [bold]pip install openai[/bold]"
            )
            return False

        if not self.api_key:
            console.print(
                "[red]Error:[/red] No API key provided for Gemini. "
                "Set the GEMINI_API_KEY environment variable or provide it in the .context file."
            )
            return False

        if not self.model:
            console.print(
                "[red]Error:[/red] No model specified for Gemini. "
                "Please specify a model in your .context file."
            )
            return False

        if not self.client:
            return False

        return True

    def _create_messages(
        self, prompt: str, system_prompt: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """
        Create the messages for the Gemini API.

        Args:
            prompt: User prompt text
            system_prompt: Optional system instructions

        Returns:
            List of message dictionaries
        """
        messages = []

        # Add system message if provided
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        # Add user message
        messages.append({"role": "user", "content": prompt})

        return messages

    def get_completion(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Get a completion from Gemini.

        Args:
            prompt: The prompt to send to the model
            system_prompt: Optional system instructions
            temperature: Temperature parameter (0.0 to 1.0)
            max_tokens: Maximum tokens to generate (None for model default)

        Returns:
            The generated completion text
        """
        if not self.validate_config():
            return "Error: Gemini provider not properly configured."

        messages = self._create_messages(prompt, system_prompt)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            return response.choices[0].message.content or ""
        except Exception as e:
            console.print(f"[red]Error getting completion from Gemini:[/red] {str(e)}")
            return f"Error: {str(e)}"

    def get_completion_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> Iterator[str]:
        """
        Stream a completion from Gemini.

        Args:
            prompt: The prompt to send to the model
            system_prompt: Optional system instructions
            temperature: Temperature parameter (0.0 to 1.0)
            max_tokens: Maximum tokens to generate (None for model default)

        Returns:
            Iterator yielding completion text chunks
        """
        if not self.validate_config():
            yield "Error: Gemini provider not properly configured."
            return

        messages = self._create_messages(prompt, system_prompt)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )

            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            console.print(
                f"[red]Error streaming completion from Gemini:[/red] {str(e)}"
            )
            yield f"Error: {str(e)}"
