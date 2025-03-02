"""Tests for the CLI interface."""

import os
import pytest
from pathlib import Path
from typer.testing import CliRunner

from dcx.cli import app
from dcx import __version__


@pytest.fixture
def runner():
    """Create a CLI runner for testing."""
    return CliRunner()


def test_version_command(runner):
    """Test the version command."""
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert f"dot-context version: {__version__}" in result.stdout


def test_init_command(runner, tmp_path):
    """Test the init command creates a .context file."""
    # Run the init command in a temporary directory
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(app, ["init"])
        assert result.exit_code == 0
        assert "Successfully created" in result.stdout

        # Check the file was created
        config_path = Path(os.getcwd()) / ".context"
        assert config_path.exists()

        # Check content
        content = config_path.read_text(encoding="utf-8")
        assert "Sets:" in content
        assert "Models:" in content


def test_init_command_with_path(runner, tmp_path):
    """Test the init command with a custom path."""
    custom_path = tmp_path / "custom"
    custom_path.mkdir()

    result = runner.invoke(app, ["init", "--path", str(custom_path)])
    assert result.exit_code == 0
    assert "Successfully created" in result.stdout

    # Check the file was created in the custom path
    config_path = custom_path / ".context"
    assert config_path.exists()


def test_init_command_file_exists(runner, tmp_path):
    """Test the init command when file already exists."""
    # Create the file first
    with runner.isolated_filesystem(temp_dir=tmp_path):
        config_path = Path(os.getcwd()) / ".context"
        with open(config_path, "w", encoding="utf-8") as f:
            f.write("# Existing config")

        # Run with no to overwrite
        result = runner.invoke(app, ["init"], input="n\n")
        assert result.exit_code == 0
        assert "already exists" in result.stdout
        assert "Initialization cancelled" in result.stdout

        # Check content was not changed
        content = config_path.read_text(encoding="utf-8")
        assert content == "# Existing config"

        # Run with yes to overwrite
        result = runner.invoke(app, ["init"], input="y\n")
        assert result.exit_code == 0
        assert "Successfully created" in result.stdout

        # Check content was changed
        content = config_path.read_text(encoding="utf-8")
        assert "Sets:" in content


def test_config_command_no_file(runner, tmp_path):
    """Test the config command when no file exists."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(app, ["config"])
        assert result.exit_code == 0
        assert "No .context file found" in result.stdout


def test_sets_list_command_no_file(runner, tmp_path):
    """Test the sets list command when no file exists."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(app, ["sets", "list"])
        assert result.exit_code == 0
        assert "No .context file found" in result.stdout


def test_sets_show_command_no_file(runner, tmp_path):
    """Test the sets show command when no file exists."""
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(app, ["sets", "show", "example"])
        assert result.exit_code == 0
        assert "No .context file found" in result.stdout


def test_sets_show_nonexistent_set(runner, example_context_file):
    """Test showing a nonexistent set."""
    result = runner.invoke(
        app, ["sets", "show", "nonexistent", "--file", str(example_context_file)]
    )
    assert result.exit_code == 0
    assert "Error" in result.stdout
    assert "not found" in result.stdout
