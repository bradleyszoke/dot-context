"""History management for dot-context queries."""

import os
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union

from rich.console import Console
from rich.table import Table
from rich.markdown import Markdown

console = Console()

# Default history file location in user's home directory
DEFAULT_HISTORY_DIR = os.path.join(os.path.expanduser("~"), ".dcx", "history")


def get_history_dir() -> Path:
    """Get the directory for history files."""
    history_dir = os.environ.get("DCX_HISTORY_DIR", DEFAULT_HISTORY_DIR)
    path = Path(history_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_query_to_history(
    query: str,
    response: str,
    set_name: str,
    model_name: str,
    files_count: int,
    token_count: int,
    execution_time: float,
) -> str:
    """
    Save a query and its response to history.

    Args:
        query: The query text
        response: The model's response
        set_name: Context set name
        model_name: Model name
        files_count: Number of files included in context
        token_count: Approximate token count
        execution_time: Time taken to execute query in seconds

    Returns:
        The ID of the saved history entry
    """
    history_dir = get_history_dir()

    # Generate a short ID (first 8 chars of a UUID)
    entry_id = str(uuid.uuid4()).split("-")[0]

    # Create a history entry
    timestamp = datetime.now().isoformat()
    entry = {
        "id": entry_id,
        "timestamp": timestamp,
        "query": query,
        "response": response,
        "set_name": set_name,
        "model_name": model_name,
        "files_count": files_count,
        "token_count": token_count,
        "execution_time": execution_time,
    }

    # Save to file
    history_file = history_dir / f"{entry_id}.json"
    with open(history_file, "w", encoding="utf-8") as f:
        json.dump(entry, f, indent=2)

    return entry_id


def get_history_entries(max_entries: int = 5) -> List[Dict[str, Any]]:
    """
    Get recent history entries, sorted by timestamp (newest first).

    Args:
        max_entries: Maximum number of entries to return

    Returns:
        List of history entries
    """
    history_dir = get_history_dir()
    entries = []

    # Get all JSON files in the history directory
    for file_path in history_dir.glob("*.json"):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                entry = json.load(f)
                entries.append(entry)
        except Exception as e:
            console.print(
                f"[yellow]Warning:[/yellow] Failed to read history file {file_path}: {str(e)}"
            )

    # Sort by timestamp (newest first)
    entries.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

    # Return only the most recent entries
    return entries[:max_entries]


def get_history_entry(entry_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a specific history entry by ID.

    Args:
        entry_id: The ID of the history entry to retrieve

    Returns:
        The history entry if found, None otherwise
    """
    history_dir = get_history_dir()
    history_file = history_dir / f"{entry_id}.json"

    if not history_file.exists():
        return None

    try:
        with open(history_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        console.print(f"[red]Error:[/red] Failed to read history file: {str(e)}")
        return None


def save_entry_to_file(entry_id: str, output_path: Union[str, Path]) -> bool:
    """
    Save a history entry to a file.

    Args:
        entry_id: The ID of the history entry to save
        output_path: Path where to save the file

    Returns:
        True if successful, False otherwise
    """
    entry = get_history_entry(entry_id)
    if not entry:
        console.print(f"[red]Error:[/red] History entry with ID '{entry_id}' not found")
        return False

    output_path = Path(output_path)

    # Determine format based on file extension
    extension = output_path.suffix.lower()

    try:
        if extension == ".json":
            # Save full entry as JSON
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(entry, f, indent=2)
        elif extension in [".md", ".markdown"]:
            # Format as markdown
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(f"# Query: {entry['query']}\n\n")
                f.write(
                    f"**Date:** {datetime.fromisoformat(entry['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}\n"
                )
                f.write(f"**Context Set:** {entry['set_name']}\n")
                f.write(f"**Model:** {entry['model_name']}\n")
                f.write(f"**Files:** {entry['files_count']}\n")
                f.write(f"**Tokens:** {entry['token_count']}\n\n")
                f.write("## Response\n\n")
                f.write(entry["response"])
        else:
            # Default to plain text
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(f"Query: {entry['query']}\n\n")
                f.write(
                    f"Date: {datetime.fromisoformat(entry['timestamp']).strftime('%Y-%m-%d %H:%M:%S')}\n"
                )
                f.write(f"Context Set: {entry['set_name']}\n")
                f.write(f"Model: {entry['model_name']}\n")
                f.write(f"Files: {entry['files_count']}\n")
                f.write(f"Tokens: {entry['token_count']}\n\n")
                f.write(f"Response:\n\n{entry['response']}")

        return True
    except Exception as e:
        console.print(f"[red]Error:[/red] Failed to save entry to file: {str(e)}")
        return False


def format_history_list_table() -> Table:
    """Create a table for displaying history entries."""
    table = Table(show_header=True)
    table.add_column("ID", style="cyan")
    table.add_column("Date", style="green")
    table.add_column("Context Set")
    table.add_column("Model")
    table.add_column("Query Preview")
    return table


def display_history_list(max_entries: int = 5) -> None:
    """
    Display a list of recent history entries.

    Args:
        max_entries: Maximum number of entries to display
    """
    entries = get_history_entries(max_entries)

    if not entries:
        console.print("[yellow]No history entries found.[/yellow]")
        return

    table = format_history_list_table()

    for entry in entries:
        # Format timestamp
        try:
            timestamp = datetime.fromisoformat(entry.get("timestamp", ""))
            date_str = timestamp.strftime("%Y-%m-%d %H:%M")
        except:
            date_str = entry.get("timestamp", "Unknown")

        # Truncate query for preview
        query = entry.get("query", "")
        query_preview = (query[:40] + "...") if len(query) > 40 else query

        table.add_row(
            entry.get("id", ""),
            date_str,
            entry.get("set_name", ""),
            entry.get("model_name", ""),
            query_preview,
        )

    console.print("\n[bold]Recent Queries:[/bold]")
    console.print(table)
    console.print("\nUse [bold]dcx history <ID>[/bold] to view full details")
    console.print(
        "Use [bold]dcx history <ID> --save <file_path>[/bold] to save to a file"
    )


def display_history_entry(entry_id: str) -> None:
    """
    Display a specific history entry.

    Args:
        entry_id: The ID of the history entry to display
    """
    entry = get_history_entry(entry_id)

    if not entry:
        console.print(f"[red]Error:[/red] History entry with ID '{entry_id}' not found")
        return

    # Format timestamp
    try:
        timestamp = datetime.fromisoformat(entry.get("timestamp", ""))
        date_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
    except:
        date_str = entry.get("timestamp", "Unknown")

    # Display header information
    console.print(f"\n[bold cyan]Query ID:[/bold cyan] {entry.get('id', '')}")
    console.print(f"[bold]Date:[/bold] {date_str}")
    console.print(f"[bold]Context Set:[/bold] {entry.get('set_name', '')}")
    console.print(f"[bold]Model:[/bold] {entry.get('model_name', '')}")
    console.print(f"[bold]Files:[/bold] {entry.get('files_count', 0)}")
    console.print(f"[bold]Approx. Tokens:[/bold] {entry.get('token_count', 0)}")

    if "execution_time" in entry:
        console.print(
            f"[bold]Execution Time:[/bold] {entry.get('execution_time', 0):.2f}s"
        )

    # Display query and response
    console.print("\n[bold]Query:[/bold]")
    console.print(entry.get("query", ""))

    console.print("\n[bold]Response:[/bold]")
    console.print(Markdown(entry.get("response", "")))
