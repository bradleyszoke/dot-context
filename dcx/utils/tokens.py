"""Token counting utilities for dot-context.

This module provides utilities for estimating token counts in text.
These are simple approximations and may differ from actual tokenization
by specific models like GPT or Claude.
"""

import re
import os
from pathlib import Path
from typing import Dict, Optional

# Simple tokenization regex pattern
# This is a simplified version that splits on whitespace and punctuation
# For production use, you would want to use a proper tokenizer from a library
TOKEN_PATTERN = re.compile(r"\b\w+\b|[^\w\s]")


def count_tokens_simple(text: str) -> int:
    """
    Estimate tokens in text using a simple regex-based approach.

    This is a rough approximation. Actual token counts may vary significantly
    between different LLM tokenizers (GPT, Claude, etc.).

    Args:
        text: The text to count tokens in

    Returns:
        Approximate token count
    """
    if not text:
        return 0

    # Find all tokens
    tokens = TOKEN_PATTERN.findall(text)
    return len(tokens)


def count_tokens_in_file(file_path: Path) -> Dict[str, int]:
    """
    Count tokens in a file.

    Args:
        file_path: Path to the file

    Returns:
        Dictionary with token count and file size in bytes
    """
    if not file_path.exists():
        return {"size_bytes": 0, "tokens": 0}

    try:
        # Get file size
        size_bytes = file_path.stat().st_size

        # Read file content
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        # Count tokens
        token_count = count_tokens_simple(content)

        return {"size_bytes": size_bytes, "tokens": token_count}
    except Exception:
        # Return zeros for any errors
        return {"size_bytes": 0, "tokens": 0}


def format_token_count(count: int) -> str:
    """
    Format token count for display.

    Args:
        count: Token count

    Returns:
        Formatted string (e.g., "1.2K" for 1200)
    """
    if count < 1000:
        return str(count)
    elif count < 1000000:
        return f"{count/1000:.1f}K"
    else:
        return f"{count/1000000:.1f}M"
