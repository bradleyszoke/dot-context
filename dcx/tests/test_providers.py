"""Tests for LLM providers."""

import os
import pytest
from unittest.mock import MagicMock, patch

from dcx.providers import get_provider, OPENAI_AVAILABLE
from dcx.providers.base import LLMProvider
from dcx.providers.openai import OpenAIProvider


@pytest.fixture
def mock_openai_config():
    """Sample OpenAI configuration."""
    return {
        "provider": "openai",
        "api-key": "test-key",
        "model": "gpt-4",
        "description": "Test model",
    }


@patch("dcx.providers.openai.OPENAI_AVAILABLE", True)
@patch("dcx.providers.openai.OpenAI")
def test_openai_provider_init(mock_openai_client, mock_openai_config):
    """Test OpenAI provider initialization."""
    # Setup the mock
    mock_client_instance = MagicMock()
    mock_openai_client.return_value = mock_client_instance

    # Create provider
    provider = OpenAIProvider(mock_openai_config)

    # Check initialization
    assert provider.model == "gpt-4"
    assert provider.api_key == "test-key"
    assert provider.client is not None
    mock_openai_client.assert_called_once_with(api_key="test-key")


@patch("dcx.providers.openai.OPENAI_AVAILABLE", True)
@patch("dcx.providers.openai.OpenAI")
def test_get_provider_openai(mock_openai_client, mock_openai_config):
    """Test getting an OpenAI provider."""
    # Setup
    mock_client_instance = MagicMock()
    mock_openai_client.return_value = mock_client_instance

    # Get provider
    provider = get_provider("openai", mock_openai_config)

    # Check provider
    assert provider is not None
    assert isinstance(provider, OpenAIProvider)
    assert provider.model == "gpt-4"


@patch("dcx.providers.OPENAI_AVAILABLE", False)
def test_get_provider_openai_not_available(mock_openai_config):
    """Test getting an OpenAI provider when the package is not available."""
    # Get provider
    provider = get_provider("openai", mock_openai_config)

    # Provider should be None when OpenAI is not available
    assert provider is None


def test_get_provider_unsupported():
    """Test getting an unsupported provider."""
    config = {"provider": "unsupported", "api-key": "test-key", "model": "test-model"}

    provider = get_provider("unsupported", config)
    assert provider is None


@patch("dcx.providers.openai.OPENAI_AVAILABLE", True)
@patch("dcx.providers.openai.OpenAI")
def test_openai_create_messages(mock_openai_client, mock_openai_config):
    """Test creating messages for OpenAI."""
    # Setup
    mock_client_instance = MagicMock()
    mock_openai_client.return_value = mock_client_instance
    provider = OpenAIProvider(mock_openai_config)

    # Test with system prompt
    messages = provider._create_messages("Test prompt", "System instructions")
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert messages[0]["content"] == "System instructions"
    assert messages[1]["role"] == "user"
    assert messages[1]["content"] == "Test prompt"

    # Test without system prompt
    messages = provider._create_messages("Test prompt")
    assert len(messages) == 1
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "Test prompt"


@patch("dcx.providers.openai.OPENAI_AVAILABLE", True)
@patch("dcx.providers.openai.OpenAI")
def test_openai_get_completion(mock_openai_client, mock_openai_config):
    """Test getting a completion from OpenAI."""
    # Setup
    mock_client_instance = MagicMock()
    mock_chat = MagicMock()
    mock_completions = MagicMock()
    mock_client_instance.chat = mock_chat
    mock_chat.completions = mock_completions

    # Setup mock response
    mock_response = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()
    mock_message.content = "Test response"
    mock_choice.message = mock_message
    mock_response.choices = [mock_choice]
    mock_completions.create.return_value = mock_response

    mock_openai_client.return_value = mock_client_instance

    # Create provider
    provider = OpenAIProvider(mock_openai_config)

    # Test get_completion
    response = provider.get_completion("Test prompt", "System instructions", 0.5, 100)

    # Verify
    assert response == "Test response"
    mock_completions.create.assert_called_once_with(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "System instructions"},
            {"role": "user", "content": "Test prompt"},
        ],
        temperature=0.5,
        max_tokens=100,
    )


@patch("dcx.providers.openai.OPENAI_AVAILABLE", True)
@patch("dcx.providers.openai.OpenAI")
def test_openai_get_completion_stream(mock_openai_client, mock_openai_config):
    """Test streaming a completion from OpenAI."""
    # Setup
    mock_client_instance = MagicMock()
    mock_chat = MagicMock()
    mock_completions = MagicMock()
    mock_client_instance.chat = mock_chat
    mock_chat.completions = mock_completions

    # Setup mock stream response
    class MockChunk:
        def __init__(self, content):
            self.choices = [MagicMock()]
            self.choices[0].delta = MagicMock()
            self.choices[0].delta.content = content

    chunks = [MockChunk("Hello"), MockChunk(" world"), MockChunk("!")]
    mock_completions.create.return_value = chunks

    mock_openai_client.return_value = mock_client_instance

    # Create provider
    provider = OpenAIProvider(mock_openai_config)

    # Test get_completion_stream
    stream = provider.get_completion_stream(
        "Test prompt", "System instructions", 0.5, 100
    )
    chunks = list(stream)

    # Verify
    assert chunks == ["Hello", " world", "!"]
    mock_completions.create.assert_called_once_with(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "System instructions"},
            {"role": "user", "content": "Test prompt"},
        ],
        temperature=0.5,
        max_tokens=100,
        stream=True,
    )
