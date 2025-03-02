"""Tests for token counting utilities."""

import os
import tempfile
import pytest
from pathlib import Path

from dcx.utils.tokens import (
    count_tokens_simple,
    count_tokens_in_file,
    format_token_count,
)


def test_count_tokens_simple():
    """Test basic token counting functionality."""
    # Empty string
    assert count_tokens_simple("") == 0

    # Simple cases
    assert count_tokens_simple("hello world") == 2
    assert (
        count_tokens_simple("one, two, three.") == 6
    )  # one , two , three . (our tokenizer counts each character)

    # More complex text
    text = "This is a test. It has multiple sentences, with varying punctuation! How many tokens?"
    # Should count words and punctuation as separate tokens
    tokens = count_tokens_simple(text)
    assert tokens > 10  # Exact count will depend on tokenization rules


@pytest.fixture
def temp_text_file():
    """Create a temporary file with test content."""
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False) as tmp:
        content = "This is a test file.\nIt has two lines and some tokens."
        tmp.write(content)
        tmp_path = Path(tmp.name)

    yield tmp_path

    # Clean up
    os.unlink(tmp_path)


def test_count_tokens_in_file(temp_text_file):
    """Test counting tokens in a file."""
    # Test counting
    result = count_tokens_in_file(temp_text_file)

    # Check structure
    assert "size_bytes" in result
    assert "tokens" in result

    # Check values
    assert result["size_bytes"] > 0
    assert result["tokens"] > 0

    # Exact count should reflect the content
    assert result["tokens"] >= 10  # Approximate number of tokens in the content


def test_count_tokens_nonexistent_file():
    """Test counting tokens in a nonexistent file."""
    result = count_tokens_in_file(Path("/nonexistent/file"))
    assert result["size_bytes"] == 0
    assert result["tokens"] == 0


def test_format_token_count():
    """Test formatting token counts."""
    # Small numbers
    assert format_token_count(0) == "0"
    assert format_token_count(42) == "42"
    assert format_token_count(999) == "999"

    # Thousands
    assert format_token_count(1000) == "1.0K"
    assert format_token_count(1500) == "1.5K"
    assert format_token_count(10500) == "10.5K"

    # Millions
    assert format_token_count(1000000) == "1.0M"
    assert format_token_count(2500000) == "2.5M"
