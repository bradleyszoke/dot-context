"""Tests for the configuration parsing functionality."""

import os
import tempfile
import pytest
from pathlib import Path

from dcx.config import load_config, _expand_env_vars


def test_expand_env_vars():
    """Test that environment variables are correctly expanded in config."""
    # Set a test environment variable
    os.environ["TEST_VAR"] = "test_value"

    # Test with a string containing an env var
    result = _expand_env_vars("prefix_${TEST_VAR}_suffix")
    assert result == "prefix_test_value_suffix"

    # Test with a dictionary containing env vars
    test_dict = {
        "key1": "value1",
        "key2": "${TEST_VAR}",
        "nested": {"key3": "prefix_${TEST_VAR}"},
    }
    result = _expand_env_vars(test_dict)
    assert result["key1"] == "value1"
    assert result["key2"] == "test_value"
    assert result["nested"]["key3"] == "prefix_test_value"

    # Test with a list containing env vars
    test_list = ["value1", "${TEST_VAR}", ["nested_${TEST_VAR}"]]
    result = _expand_env_vars(test_list)
    assert result[0] == "value1"
    assert result[1] == "test_value"
    assert result[2][0] == "nested_test_value"


@pytest.fixture
def temp_config_file():
    """Create a temporary configuration file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False) as tmp:
        tmp.write(
            """
Sets:
  test_set:
    match:
      - "*.md"
    description: "Test set"

Models:
  test_model:
    provider: test
    api-key: test_key
    model: test-model
    description: "Test model"
"""
        )
        tmp_path = Path(tmp.name)

    yield tmp_path

    # Clean up after test
    os.unlink(tmp_path)


def test_load_config(temp_config_file):
    """Test loading a config file."""
    # Load the config
    config = load_config(temp_config_file)

    # Check the structure
    assert "Sets" in config
    assert "Models" in config

    # Check the set
    assert "test_set" in config["Sets"]
    assert config["Sets"]["test_set"]["description"] == "Test set"
    assert config["Sets"]["test_set"]["match"] == ["*.md"]

    # Check the model
    assert "test_model" in config["Models"]
    assert config["Models"]["test_model"]["provider"] == "test"
    assert config["Models"]["test_model"]["api-key"] == "test_key"
    assert config["Models"]["test_model"]["model"] == "test-model"
    assert config["Models"]["test_model"]["description"] == "Test model"


def test_load_config_file_not_found():
    """Test that FileNotFoundError is raised when config file is not found."""
    with pytest.raises(FileNotFoundError):
        load_config(Path("/path/that/does/not/exist/.context"))
