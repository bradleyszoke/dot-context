"""Tests for the CLI query command."""

import pytest
from unittest.mock import patch
from typer.testing import CliRunner

from dcx.cli import app


@pytest.fixture
def runner():
    """Create a CLI runner for testing."""
    return CliRunner()


@patch("dcx.cli.execute_query")
def test_query_command(mock_execute_query, runner):
    """Test the query command."""
    result = runner.invoke(
        app,
        [
            "query",
            "What does this code do?",
            "--set",
            "code",
            "--model",
            "openai",
            "--temperature",
            "0.5",
            "--max-tokens",
            "1000",
            "--no-stream",
        ],
    )

    assert result.exit_code == 0
    mock_execute_query.assert_called_once_with(
        query="What does this code do?",
        set_name="code",
        model_name="openai",
        system_prompt=None,
        temperature=0.5,
        max_tokens=1000,
        stream=False,
        include_filenames=True,
        config_path=None,
    )


@patch("dcx.cli.execute_query")
def test_query_command_with_system_prompt(mock_execute_query, runner):
    """Test the query command with a system prompt."""
    result = runner.invoke(
        app,
        [
            "query",
            "What does this code do?",
            "--set",
            "code",
            "--model",
            "openai",
            "--system",
            "You are a helpful assistant.",
            "--hide-filenames",
        ],
    )

    assert result.exit_code == 0
    mock_execute_query.assert_called_once_with(
        query="What does this code do?",
        set_name="code",
        model_name="openai",
        system_prompt="You are a helpful assistant.",
        temperature=0.7,  # Default
        max_tokens=None,  # Default
        stream=True,  # Default
        include_filenames=False,
        config_path=None,
    )
