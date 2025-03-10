"""Query handling for dot-context."""

import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

from rich.console import Console
from rich.markdown import Markdown
from rich.live import Live
from rich.text import Text

from .config import load_config
from .context_sets import get_context_set_files, load_context_sets
from .providers import get_provider
from .utils.tokens import count_tokens_in_file, format_token_count

console = Console()


def format_context_from_files(files: List[Path]) -> Tuple[str, int]:
    """
    Format a list of files into a context string.

    Args:
        files: List of file paths to include in the context

    Returns:
        Tuple of (formatted context string, total token count)
    """
    context_parts = []
    total_tokens = 0

    for file_path in files:
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()

            # Get relative path for display
            rel_path = Path(os.path.relpath(file_path))
            file_info = count_tokens_in_file(file_path)
            total_tokens += file_info["tokens"]

            # Format file content with header
            file_header = f"# {rel_path}\n\n"
            file_section = f"{file_header}{content}\n\n"

            context_parts.append(file_section)
        except Exception as e:
            console.print(f"[red]Error reading file {file_path}:[/red] {str(e)}")

    return "\n".join(context_parts), total_tokens


def create_prompt(context: str, query: str, include_filenames: bool = True) -> str:
    """
    Create a formatted prompt with context and query.

    Args:
        context: The context text from files
        query: The user's query
        include_filenames: Whether to include filenames in context

    Returns:
        Formatted prompt string
    """
    # Simple prompt format, can be enhanced later
    if include_filenames:
        prompt = f"Below is the context from my project files:\n\n{context}\n\nMy question is: {query}\n\nPlease respond to my question based on the provided context."
    else:
        # Strip out the filename headers if not wanted
        # This is a very simple implementation and could be improved
        import re

        context_without_headers = re.sub(r"# .*?\n\n", "", context)
        prompt = f"Below is the context from my project:\n\n{context_without_headers}\n\nMy question is: {query}\n\nPlease respond to my question based on the provided context."

    return prompt


def format_context_from_multiple_sets(
    set_names: List[str], config_path: Optional[Path] = None
) -> Tuple[str, int]:
    """
    Format context from multiple context sets.

    Args:
        set_names: List of set names to include
        config_path: Path to the .context file

    Returns:
        Tuple of (formatted context string, total token count)
    """
    all_files = []
    for set_name in set_names:
        try:
            files = get_context_set_files(set_name, config_path)
            all_files.extend(files)
        except KeyError:
            console.print(
                f"[yellow]Warning:[/yellow] Context set '{set_name}' not found"
            )

    # Remove duplicates while preserving order
    unique_files = []
    seen = set()
    for file in all_files:
        if file not in seen:
            seen.add(file)
            unique_files.append(file)

    return format_context_from_files(unique_files)


def execute_query(
    query: str,
    set_name: str,
    model_name: str,
    system_prompt: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    stream: bool = True,
    include_filenames: bool = True,
    config_path: Optional[Path] = None,
) -> None:
    """
    Execute a query against a model with given context.

    Args:
        query: The query to send to the model
        set_name: Name of the context set to use (can be comma-separated for multiple sets)
        model_name: Name of the model to use
        system_prompt: Optional system instructions
        temperature: Model temperature (0.0 to 1.0)
        max_tokens: Maximum tokens to generate
        stream: Whether to stream the response
        include_filenames: Whether to include filenames in context
        config_path: Path to config file
    """
    try:
        # Load config and files
        config = load_config(config_path)

        # Validate the model exists
        if "Models" not in config or model_name not in config["Models"]:
            console.print(
                f"[red]Error:[/red] Model '{model_name}' not found in configuration"
            )
            return

        model_config = config["Models"][model_name]

        # Check if we have multiple sets (comma-separated)
        set_names = [s.strip() for s in set_name.split(",")]

        if len(set_names) > 1:
            # Multiple sets specified
            context, total_tokens = format_context_from_multiple_sets(
                set_names, config_path
            )
            files_count = sum(
                len(get_context_set_files(s, config_path))
                for s in set_names
                if s in load_context_sets(config_path)
            )
            set_display = ", ".join(set_names)
        else:
            # Single set specified
            try:
                files = get_context_set_files(set_name, config_path)
                files_count = len(files)
            except KeyError:
                console.print(f"[red]Error:[/red] Context set '{set_name}' not found")
                return

            if not files:
                console.print(
                    f"[yellow]Warning:[/yellow] No files found in context set '{set_name}'"
                )
                proceed = console.input(
                    "Do you want to proceed with an empty context? [y/N]: "
                ).lower()
                if proceed != "y":
                    console.print("Query cancelled.")
                    return
                context = ""
                total_tokens = 0
            else:
                context, total_tokens = format_context_from_files(files)

            set_display = set_name

        # Get the provider
        provider = get_provider(model_name, model_config)
        if not provider:
            console.print(
                f"[red]Error:[/red] Unable to initialize provider for '{model_name}'"
            )
            return

        if not provider.validate_config():
            return

        # Create prompt
        prompt = create_prompt(context, query, include_filenames)

        # Display query information
        console.print(
            f"\n[bold]Context:[/bold] {set_display} ({files_count} files, ~{format_token_count(total_tokens)} tokens)"
        )
        console.print(
            f"[bold]Model:[/bold] {model_name} ({model_config.get('provider', 'unknown')})"
        )
        console.print(f"[bold]Query:[/bold] {query}\n")

        # Display "Thinking..." message and execute query
        if stream:
            # First show thinking status
            with console.status("[bold cyan]Thinking...[/bold cyan]"):
                # Prepare response but don't stream yet
                stream_generator = provider.get_completion_stream(
                    prompt, system_prompt, temperature, max_tokens
                )
                # Force initial connection/response
                stream_iterator = iter(stream_generator)
                try:
                    first_chunk = next(stream_iterator)
                except StopIteration:
                    first_chunk = ""

            # Then show response with streaming
            console.print("[bold cyan]Response:[/bold cyan]")
            response_text = first_chunk

            # Use Live display for streaming (after the status context is closed)
            with Live(console=console, refresh_per_second=10) as live:
                live.update(Markdown(response_text))

                # Continue with the rest of the stream
                for chunk in stream_iterator:
                    response_text += chunk
                    live.update(Markdown(response_text))
        else:
            # Non-streaming mode
            with console.status("[bold cyan]Thinking...[/bold cyan]"):
                response = provider.get_completion(
                    prompt, system_prompt, temperature, max_tokens
                )

            console.print("[bold cyan]Response:[/bold cyan]")
            console.print(Markdown(response))

        console.print("\n[dim]Query complete.[/dim]")

    except Exception as e:
        console.print(f"[red]Error executing query:[/red] {str(e)}")
