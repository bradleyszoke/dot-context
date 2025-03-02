"""Tests for the query functionality."""

import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from dcx.query import format_context_from_files, create_prompt, execute_query


@pytest.fixture
def test_files():
    """Create temporary files for testing."""
    files = []

    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f1:
        f1.write("Test content for file 1")
        files.append(Path(f1.name))

    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f2:
        f2.write("Test content for file 2")
        files.append(Path(f2.name))

    yield files

    # Clean up
    for file_path in files:
        if file_path.exists():
            os.unlink(file_path)


def test_format_context_from_files(test_files):
    """Test formatting context from files."""
    # Format context
    context, tokens = format_context_from_files(test_files)

    # Verify content
    for file_path in test_files:
        assert file_path.name in context
        assert "Test content for file" in context

    # Tokens should be greater than 0
    assert tokens > 0


def test_create_prompt():
    """Test creating prompts with context."""
    # Test with filenames
    context = "# file1.py\n\ndef test():\n    pass\n\n# file2.py\n\nprint('hello')"
    query = "How many files are there?"

    prompt = create_prompt(context, query, include_filenames=True)

    assert "# file1.py" in prompt
    assert "# file2.py" in prompt
    assert "How many files are there?" in prompt

    # Test without filenames
    prompt = create_prompt(context, query, include_filenames=False)

    assert "# file1.py" not in prompt
    assert "# file2.py" not in prompt
    assert "def test():" in prompt
    assert "print('hello')" in prompt
    assert "How many files are there?" in prompt


@patch("dcx.query.load_config")
@patch("dcx.query.get_context_set_files")
@patch("dcx.query.get_provider")
def test_execute_query(mock_get_provider, mock_get_files, mock_load_config, test_files):
    """Test executing a query."""
    # Mock config
    mock_config = {
        "Models": {
            "test_model": {
                "provider": "openai",
                "api-key": "test-key",
                "model": "gpt-4",
            }
        }
    }
    mock_load_config.return_value = mock_config

    # Mock files
    mock_get_files.return_value = test_files

    # Mock provider
    mock_provider = MagicMock()
    mock_provider.validate_config.return_value = True
    mock_provider.get_completion.return_value = "Test response"
    mock_get_provider.return_value = mock_provider

    # Execute query (non-streaming)
    execute_query(
        "Test query",
        "test_set",
        "test_model",
        system_prompt="Test system prompt",
        temperature=0.5,
        max_tokens=100,
        stream=False,
    )

    # Verify
    mock_load_config.assert_called_once()
    mock_get_files.assert_called_once_with("test_set", None)
    mock_get_provider.assert_called_once_with(
        "test_model", mock_config["Models"]["test_model"]
    )
    mock_provider.validate_config.assert_called_once()

    # Check the prompt contains the content from files
    call_args = mock_provider.get_completion.call_args[0]
    prompt = call_args[0]
    for file_path in test_files:
        assert file_path.name in prompt
    assert "Test query" in prompt

    # Check other parameters
    assert call_args[1] == "Test system prompt"
    assert call_args[2] == 0.5
    assert call_args[3] == 100


@patch("dcx.query.load_config")
@patch("dcx.query.get_context_set_files")
@patch("dcx.query.get_provider")
@patch("dcx.query.Live")  # Mock the rich.live.Live class
def test_execute_query_stream(
    mock_live, mock_get_provider, mock_get_files, mock_load_config, test_files
):
    """Test executing a streaming query."""
    # Mock config
    mock_config = {
        "Models": {
            "test_model": {
                "provider": "openai",
                "api-key": "test-key",
                "model": "gpt-4",
            }
        }
    }
    mock_load_config.return_value = mock_config

    # Mock files
    mock_get_files.return_value = test_files

    # Mock provider
    mock_provider = MagicMock()
    mock_provider.validate_config.return_value = True
    mock_provider.get_completion_stream.return_value = ["Test ", "response ", "chunks"]
    mock_get_provider.return_value = mock_provider

    # Mock Live context manager
    mock_live_instance = MagicMock()
    mock_live.return_value.__enter__.return_value = mock_live_instance

    # Execute query (streaming)
    execute_query(
        "Test query",
        "test_set",
        "test_model",
        system_prompt="Test system prompt",
        temperature=0.5,
        max_tokens=100,
        stream=True,
    )

    # Verify
    mock_load_config.assert_called_once()
    mock_get_files.assert_called_once_with("test_set", None)
    mock_get_provider.assert_called_once_with(
        "test_model", mock_config["Models"]["test_model"]
    )
    mock_provider.validate_config.assert_called_once()

    # Check the streaming function was called
    assert mock_provider.get_completion_stream.called

    # Check the prompt contains the content from files
    call_args = mock_provider.get_completion_stream.call_args[0]
    prompt = call_args[0]
    for file_path in test_files:
        assert file_path.name in prompt
    assert "Test query" in prompt

    # Check other parameters
    assert call_args[1] == "Test system prompt"
    assert call_args[2] == 0.5
    assert call_args[3] == 100


@patch("dcx.query.load_config")
def test_execute_query_model_not_found(mock_load_config):
    """Test executing a query with a model that doesn't exist."""
    # Mock config with no models
    mock_config = {"Models": {}}
    mock_load_config.return_value = mock_config

    # Execute query
    execute_query("Test query", "test_set", "nonexistent_model")

    # Only load_config should be called
    mock_load_config.assert_called_once()


@patch("dcx.query.load_config")
@patch("dcx.query.get_context_set_files")
def test_execute_query_set_not_found(mock_get_files, mock_load_config):
    """Test executing a query with a context set that doesn't exist."""
    # Mock config
    mock_config = {
        "Models": {
            "test_model": {
                "provider": "openai",
                "api-key": "test-key",
                "model": "gpt-4",
            }
        }
    }
    mock_load_config.return_value = mock_config

    # Mock set not found
    mock_get_files.side_effect = KeyError("test_set not found")

    # Execute query
    execute_query("Test query", "nonexistent_set", "test_model")

    # Verify
    mock_load_config.assert_called_once()
    mock_get_files.assert_called_once()
