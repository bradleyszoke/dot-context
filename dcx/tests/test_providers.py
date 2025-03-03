"""Tests for LLM providers."""

import os
import pytest
from unittest.mock import MagicMock, patch

from dcx.providers import get_provider
from dcx.providers.base import LLMProvider
from dcx.providers.openai import OpenAIProvider
from dcx.providers.anthropic import AnthropicProvider
from dcx.providers.gemini import GeminiProvider, GEMINI_BASE_URL


# --- Provider Config Fixtures ---


@pytest.fixture
def mock_openai_config():
    """Sample OpenAI configuration."""
    return {
        "provider": "openai",
        "api-key": "test-key",
        "model": "gpt-4",
        "description": "Test model",
    }


@pytest.fixture
def mock_anthropic_config():
    """Sample Anthropic configuration."""
    return {
        "provider": "anthropic",
        "api-key": "test-key",
        "model": "claude-3-opus-20240229",
        "description": "Test model",
    }


@pytest.fixture
def mock_gemini_config():
    """Sample Gemini configuration."""
    return {
        "provider": "gemini",
        "api-key": "test-key",
        "model": "gemini-2.0-flash",
        "description": "Test model",
    }


# --- Provider Parameters ---

PROVIDER_PARAMS = [
    {
        "name": "openai",
        "config_fixture": "mock_openai_config",
        "module_path": "dcx.providers.openai",
        "client_class": "OpenAI",
        "provider_class": OpenAIProvider,
        "available_var": "OPENAI_AVAILABLE",
    },
    {
        "name": "anthropic",
        "config_fixture": "mock_anthropic_config",
        "module_path": "dcx.providers.anthropic",
        "client_class": "Anthropic",
        "provider_class": AnthropicProvider,
        "available_var": "ANTHROPIC_AVAILABLE",
    },
    {
        "name": "gemini",
        "config_fixture": "mock_gemini_config",
        "module_path": "dcx.providers.gemini",
        "client_class": "OpenAI",  # Gemini uses OpenAI client through compatibility layer
        "provider_class": GeminiProvider,
        "available_var": "OPENAI_AVAILABLE",
        "base_url": GEMINI_BASE_URL,  # Special case for Gemini
    },
]


# --- Test Provider Initialization ---


@pytest.mark.parametrize("provider_param", PROVIDER_PARAMS)
def test_provider_init(request, provider_param):
    """Test provider initialization."""
    # Get the config from the fixture
    config = request.getfixturevalue(provider_param["config_fixture"])
    provider_class = provider_param["provider_class"]

    # Create patches
    available_patch = patch(
        f"{provider_param['module_path']}.{provider_param['available_var']}", True
    )
    client_patch = patch(
        f"{provider_param['module_path']}.{provider_param['client_class']}"
    )

    # Apply patches
    available_patch.start()
    mock_client = client_patch.start()

    try:
        # Setup the mock
        mock_client_instance = MagicMock()
        mock_client.return_value = mock_client_instance

        # Create provider
        provider = provider_class(config)

        # Check initialization
        assert provider.model == config["model"]
        assert provider.api_key == "test-key"
        assert provider.client is not None

        # Check client initialization (special case for Gemini with base_url)
        if "base_url" in provider_param:
            mock_client.assert_called_once_with(
                api_key="test-key", base_url=provider_param["base_url"]
            )
        else:
            mock_client.assert_called_once_with(api_key="test-key")

    finally:
        # Clean up patches
        available_patch.stop()
        client_patch.stop()


# --- Test Get Provider ---


@pytest.mark.parametrize("provider_param", PROVIDER_PARAMS)
def test_get_provider(request, provider_param):
    """Test getting a provider instance."""
    # Get the config from the fixture
    config = request.getfixturevalue(provider_param["config_fixture"])
    provider_class = provider_param["provider_class"]

    # Create patches
    module_available_patch = patch(
        f"dcx.providers.{provider_param['available_var']}", True
    )
    provider_available_patch = patch(
        f"{provider_param['module_path']}.{provider_param['available_var']}", True
    )
    client_patch = patch(
        f"{provider_param['module_path']}.{provider_param['client_class']}"
    )

    # Apply patches
    module_available_patch.start()
    provider_available_patch.start()
    mock_client = client_patch.start()

    try:
        # Setup the mock
        mock_client_instance = MagicMock()
        mock_client.return_value = mock_client_instance

        # Get provider
        provider = get_provider(provider_param["name"], config)

        # Check provider
        assert provider is not None
        assert isinstance(provider, provider_class)
        assert provider.model == config["model"]

    finally:
        # Clean up patches
        module_available_patch.stop()
        provider_available_patch.stop()
        client_patch.stop()


# --- Test Provider Not Available ---


@pytest.mark.parametrize("provider_param", PROVIDER_PARAMS)
def test_provider_not_available(request, provider_param):
    """Test provider not available."""
    # Get the config from the fixture
    config = request.getfixturevalue(provider_param["config_fixture"])

    # Create patch for the provider not being available at module level
    with patch(f"dcx.providers.{provider_param['available_var']}", False):
        # Get provider
        provider = get_provider(provider_param["name"], config)

        # Provider should be None when package is not available
        assert provider is None


# --- Test Completion Methods ---


def _get_completion_test_params():
    """Generate test parameters for get_completion tests."""
    test_params = []

    # OpenAI completion test parameters
    test_params.append(
        {
            "provider_param": PROVIDER_PARAMS[0],  # OpenAI
            "setup_mock": lambda mock_client: _setup_openai_completion_mock(
                mock_client
            ),
            "expected_response": "Test response",
            "expected_call": _verify_openai_completion_call,
        }
    )

    # Anthropic completion test parameters
    test_params.append(
        {
            "provider_param": PROVIDER_PARAMS[1],  # Anthropic
            "setup_mock": lambda mock_client: _setup_anthropic_completion_mock(
                mock_client
            ),
            "expected_response": "Test response",
            "expected_call": _verify_anthropic_completion_call,
        }
    )

    # Gemini completion test parameters (uses OpenAI client)
    test_params.append(
        {
            "provider_param": PROVIDER_PARAMS[2],  # Gemini
            "setup_mock": lambda mock_client: _setup_openai_completion_mock(
                mock_client
            ),
            "expected_response": "Test response",
            "expected_call": _verify_openai_completion_call,
        }
    )

    return test_params


def _setup_openai_completion_mock(mock_client):
    """Setup mock for OpenAI completion."""
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

    return mock_client_instance


def _verify_openai_completion_call(
    mock_create, model, messages, temperature, max_tokens
):
    """Verify OpenAI completion call."""
    mock_create.assert_called_once_with(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )


def _setup_anthropic_completion_mock(mock_client):
    """Setup mock for Anthropic completion."""
    mock_client_instance = MagicMock()
    mock_messages = MagicMock()
    mock_client_instance.messages = mock_messages

    # Setup mock response
    mock_response = MagicMock()
    mock_content = MagicMock()
    mock_content.text = "Test response"
    mock_response.content = [mock_content]
    mock_messages.create.return_value = mock_response

    return mock_client_instance


def _verify_anthropic_completion_call(
    mock_create, model, messages, temperature, max_tokens
):
    """Verify Anthropic completion call."""
    mock_create.assert_called_once_with(
        model=model,
        messages=messages,
        system="System instructions",
        temperature=temperature,
        max_tokens=max_tokens,
    )


@pytest.mark.parametrize("test_param", _get_completion_test_params())
def test_get_completion(request, test_param):
    """Test get_completion method for providers."""
    provider_param = test_param["provider_param"]

    # Get the config from the fixture
    config = request.getfixturevalue(provider_param["config_fixture"])
    provider_class = provider_param["provider_class"]

    # Create patches
    available_patch = patch(
        f"{provider_param['module_path']}.{provider_param['available_var']}", True
    )
    client_patch = patch(
        f"{provider_param['module_path']}.{provider_param['client_class']}"
    )

    # Apply patches
    available_patch.start()
    mock_client = client_patch.start()

    try:
        # Setup the mock client
        mock_client_instance = test_param["setup_mock"](mock_client)
        mock_client.return_value = mock_client_instance

        # Create provider
        provider = provider_class(config)

        # Test get_completion
        response = provider.get_completion(
            "Test prompt", "System instructions", 0.5, 100
        )

        # Verify response
        assert response == test_param["expected_response"]

        # Different path to the create method based on provider
        if provider_param["name"] == "openai" or provider_param["name"] == "gemini":
            mock_create = mock_client_instance.chat.completions.create
            expected_messages = [
                {"role": "system", "content": "System instructions"},
                {"role": "user", "content": "Test prompt"},
            ]
        else:  # anthropic
            mock_create = mock_client_instance.messages.create
            expected_messages = [{"role": "user", "content": "Test prompt"}]

        # Verify call
        test_param["expected_call"](
            mock_create, config["model"], expected_messages, 0.5, 100
        )

    finally:
        # Clean up patches
        available_patch.stop()
        client_patch.stop()


# --- Test Streaming Methods ---


def _get_streaming_test_params():
    """Generate test parameters for streaming tests."""
    test_params = []

    # OpenAI streaming test parameters
    test_params.append(
        {
            "provider_param": PROVIDER_PARAMS[0],  # OpenAI
            "setup_mock": lambda mock_client: _setup_openai_streaming_mock(mock_client),
            "expected_chunks": ["Hello", " world", "!"],
            "expected_call": _verify_openai_streaming_call,
        }
    )

    # Anthropic streaming test parameters
    test_params.append(
        {
            "provider_param": PROVIDER_PARAMS[1],  # Anthropic
            "setup_mock": lambda mock_client: _setup_anthropic_streaming_mock(
                mock_client
            ),
            "expected_chunks": ["Hello", " world", "!"],
            "expected_call": _verify_anthropic_streaming_call,
        }
    )

    # Gemini streaming test parameters (uses OpenAI client)
    test_params.append(
        {
            "provider_param": PROVIDER_PARAMS[2],  # Gemini
            "setup_mock": lambda mock_client: _setup_openai_streaming_mock(mock_client),
            "expected_chunks": ["Hello", " world", "!"],
            "expected_call": _verify_openai_streaming_call,
        }
    )

    return test_params


def _setup_openai_streaming_mock(mock_client):
    """Setup mock for OpenAI streaming."""
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

    return mock_client_instance


def _verify_openai_streaming_call(
    mock_create, model, messages, temperature, max_tokens
):
    """Verify OpenAI streaming call."""
    mock_create.assert_called_once_with(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        stream=True,
    )


def _setup_anthropic_streaming_mock(mock_client):
    """Setup mock for Anthropic streaming."""
    mock_client_instance = MagicMock()
    mock_messages = MagicMock()
    mock_client_instance.messages = mock_messages

    # Setup mock stream
    mock_stream = MagicMock()
    mock_stream_instance = MagicMock()
    mock_stream_instance.text_stream = iter(["Hello", " world", "!"])
    mock_stream.__enter__.return_value = mock_stream_instance
    mock_messages.stream.return_value = mock_stream

    return mock_client_instance


def _verify_anthropic_streaming_call(
    mock_create, model, messages, temperature, max_tokens
):
    """Verify Anthropic streaming call."""
    mock_create.assert_called_once_with(
        model=model,
        messages=messages,
        system="System instructions",
        temperature=temperature,
        max_tokens=max_tokens,
    )


@pytest.mark.parametrize("test_param", _get_streaming_test_params())
def test_get_completion_stream(request, test_param):
    """Test streaming completions from provider."""
    provider_param = test_param["provider_param"]

    # Get the config from the fixture
    config = request.getfixturevalue(provider_param["config_fixture"])
    provider_class = provider_param["provider_class"]

    # Create patches
    available_patch = patch(
        f"{provider_param['module_path']}.{provider_param['available_var']}", True
    )
    client_patch = patch(
        f"{provider_param['module_path']}.{provider_param['client_class']}"
    )

    # Apply patches
    available_patch.start()
    mock_client = client_patch.start()

    try:
        # Setup mock client
        mock_client_instance = test_param["setup_mock"](mock_client)
        mock_client.return_value = mock_client_instance

        # Create provider
        provider = provider_class(config)

        # Test get_completion_stream
        stream = provider.get_completion_stream(
            "Test prompt", "System instructions", 0.5, 100
        )
        chunks = list(stream)  # Consume the stream

        # Verify response
        assert chunks == test_param["expected_chunks"]

        # Different path to the create method based on provider
        if provider_param["name"] == "openai" or provider_param["name"] == "gemini":
            mock_create = mock_client_instance.chat.completions.create
            expected_messages = [
                {"role": "system", "content": "System instructions"},
                {"role": "user", "content": "Test prompt"},
            ]
        else:  # anthropic
            mock_create = mock_client_instance.messages.stream
            expected_messages = [{"role": "user", "content": "Test prompt"}]

        # Verify call
        test_param["expected_call"](
            mock_create, config["model"], expected_messages, 0.5, 100
        )

    finally:
        # Clean up patches
        available_patch.stop()
        client_patch.stop()


# --- Test unsupported provider ---


def test_get_provider_unsupported():
    """Test getting an unsupported provider."""
    config = {"provider": "unsupported", "api-key": "test-key", "model": "test-model"}

    provider = get_provider("unsupported", config)
    assert provider is None
