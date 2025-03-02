"""Tests for the context sets functionality."""

import os
import tempfile
import pytest
from pathlib import Path

from dcx.context_sets import ContextSet, load_context_sets


@pytest.fixture
def test_dir():
    """Create a temporary directory with test files for testing context sets."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        base_dir = Path(tmp_dir)

        # Create some test files
        create_test_file(base_dir, "file1.md", "Test content 1")
        create_test_file(base_dir, "file2.md", "Test content 2")
        create_test_file(base_dir, "subfolder/file3.md", "Test content 3")
        create_test_file(base_dir, "file4.txt", "Test content 4")

        # Create a test .context file
        config_path = base_dir / ".context"
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(
                """
Sets:
  markdown:
    match:
      - "*.md"
    description: "Markdown files"
  
  subfolder:
    match:
      - "subfolder/*.md"
    description: "Subfolder files"
    
  combined:
    include:
      - markdown
      - subfolder
    description: "Combined set"
    
  with_pattern:
    match:
      - "*.txt"
    include:
      - markdown
    description: "With pattern and include"
    
Models:
  test_model:
    provider: test
    api-key: test_key
    model: test-model
    description: "Test model"
"""
            )

        yield {"base_dir": base_dir, "config_path": config_path}


def create_test_file(base_dir, relative_path, content):
    """Create a test file with the given relative path and content."""
    file_path = base_dir / relative_path
    os.makedirs(file_path.parent, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)


def test_context_set_direct_match(test_dir):
    """Test matching files with direct patterns."""
    base_dir = test_dir["base_dir"]
    config = {"match": ["*.md"], "description": "Test set"}
    test_set = ContextSet("test", config, base_dir)

    files = test_set.get_matching_files()
    file_names = {f.name for f in files}

    assert len(files) == 2
    assert "file1.md" in file_names
    assert "file2.md" in file_names


def test_context_set_subfolder_match(test_dir):
    """Test matching files in subfolders."""
    base_dir = test_dir["base_dir"]
    config = {"match": ["subfolder/*.md"], "description": "Test set"}
    test_set = ContextSet("test", config, base_dir)

    files = test_set.get_matching_files()
    file_names = {f.name for f in files}

    assert len(files) == 1
    assert "file3.md" in file_names


def test_context_set_include(test_dir):
    """Test including other sets."""
    config_path = test_dir["config_path"]
    all_sets = load_context_sets(config_path)
    combined_set = all_sets["combined"]

    files = combined_set.get_matching_files(all_sets)
    file_names = {f.name for f in files}

    assert len(files) == 3
    assert "file1.md" in file_names
    assert "file2.md" in file_names
    assert "file3.md" in file_names


def test_context_set_with_pattern_and_include(test_dir):
    """Test a set with both pattern and include."""
    config_path = test_dir["config_path"]
    all_sets = load_context_sets(config_path)
    set_with_both = all_sets["with_pattern"]

    files = set_with_both.get_matching_files(all_sets)
    file_names = {f.name for f in files}

    assert len(files) == 3
    assert "file1.md" in file_names
    assert "file2.md" in file_names
    assert "file4.txt" in file_names


def test_load_context_sets(test_dir):
    """Test loading all context sets from config."""
    config_path = test_dir["config_path"]
    all_sets = load_context_sets(config_path)

    assert len(all_sets) == 4
    assert "markdown" in all_sets
    assert "subfolder" in all_sets
    assert "combined" in all_sets
    assert "with_pattern" in all_sets

    # Check the description of a set
    assert all_sets["markdown"].description == "Markdown files"


def test_missing_context_set(test_dir):
    """Test that KeyError is raised for a missing context set."""
    config_path = test_dir["config_path"]
    with pytest.raises(KeyError):
        from dcx.context_sets import get_context_set_files

        get_context_set_files("nonexistent_set", config_path)
