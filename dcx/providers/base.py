"""Base provider interface for LLM providers."""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Iterator


class LLMProvider(ABC):
    """Base class for LLM providers."""

    @abstractmethod
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the provider with configuration.

        Args:
            config: Configuration dictionary from the .context file
        """
        pass

    @abstractmethod
    def validate_config(self) -> bool:
        """
        Validate that the provider has all required configuration.

        Returns:
            True if configuration is valid, False otherwise
        """
        pass

    @abstractmethod
    def get_completion(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Get a completion from the LLM.

        Args:
            prompt: The prompt to send to the LLM
            system_prompt: Optional system prompt or instructions
            temperature: Temperature parameter (0.0 to 1.0)
            max_tokens: Maximum tokens to generate (None for model default)

        Returns:
            The generated completion text
        """
        pass

    @abstractmethod
    def get_completion_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> Iterator[str]:
        """
        Stream a completion from the LLM.

        Args:
            prompt: The prompt to send to the LLM
            system_prompt: Optional system prompt or instructions
            temperature: Temperature parameter (0.0 to 1.0)
            max_tokens: Maximum tokens to generate (None for model default)

        Returns:
            Iterator yielding completion text chunks
        """
        pass
