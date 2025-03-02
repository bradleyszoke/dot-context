"""Shared pytest fixtures and configurations."""

import os
import pytest
from pathlib import Path
import tempfile


@pytest.fixture(autouse=True)
def cleanup_env_vars():
    """
    Fixture to clean up any environment variables set during tests.
    This runs automatically for all tests.
    """
    # Store original environment
    original_environ = dict(os.environ)

    # Run the test
    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_environ)


@pytest.fixture
def example_context_file():
    """Create a simple example .context file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False) as tmp:
        tmp.write(
            """
Sets:
  docs:
    match:
      - "docs/**/*.md"
    description: "Documentation files"
  
  code:
    match:
      - "**/*.py"
    description: "Python code files"

Models:
  sample:
    provider: example
    api-key: ${EXAMPLE_API_KEY}
    model: test-model
    description: "Test model"
"""
        )
        tmp_path = Path(tmp.name)

    yield tmp_path

    # Clean up after test
    if tmp_path.exists():
        os.unlink(tmp_path)
