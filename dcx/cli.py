"""Command-line interface for the dot-context tool."""

import typer
from rich.console import Console
from rich.table import Table
from rich.markdown import Markdown
from pathlib import Path
from typing import Optional, List

# Import version at the module level
from . import __version__
from .config import load_config, find_config_file
from .context_sets import load_context_sets, get_context_set_files
from .utils.tokens import count_tokens_in_file, format_token_count
from .query import execute_query

app = typer.Typer(help="A CLI tool for configurable LLM context")
console = Console()


@app.callback()
def callback():
    """A CLI tool for configurable LLM context."""


@app.command()
def version():
    """Show the version of dot-context."""
    console.print(f"dot-context version: {__version__}")


@app.command()
def init(
    path: Optional[Path] = typer.Option(
        None, "--path", "-p", help="Path where to create the .context file"
    )
):
    """Initialize a new .context configuration file."""
    target_path = Path.cwd() if path is None else path
    config_path = target_path / ".context"

    if config_path.exists():
        console.print(
            f"[yellow]Warning:[/yellow] .context file already exists at {config_path}"
        )
        overwrite = typer.confirm("Do you want to overwrite it?")
        if not overwrite:
            console.print("Initialization cancelled.")
            return

    # Sample configuration
    sample_config = """# Dot Context Configuration

Sets:
  example:
    match:
      - "*.md"
    description: "Example context set matching all markdown files"

  code:
    match:
      - "**/*.py"
    description: "All Python code files"

Models:
  # You MUST specify a valid model name for each provider
  # Model names change over time, check provider documentation for current options
  openai:
    provider: openai
    api-key: ${OPENAI_API_KEY}
    model: gpt-4           # Replace with your desired OpenAI model
    description: "OpenAI model"
    
  claude:
    provider: anthropic
    api-key: ${ANTHROPIC_API_KEY}
    model: claude-3-opus   # Replace with your desired Anthropic model
    description: "Anthropic Claude model"
    
  gemini:
    provider: gemini
    api-key: ${GEMINI_API_KEY}
    model: gemini-2.0-flash # Replace with your desired Gemini model
    description: "Google Gemini model (using OpenAI compatibility)"
"""

    with open(config_path, "w", encoding="utf-8") as f:
        f.write(sample_config)

    console.print(f"[green]Successfully created[/green] .context file at {config_path}")
    console.print("\nTo use this configuration:")
    console.print("1. Set your API keys as environment variables:")
    console.print("   export OPENAI_API_KEY=your_api_key_here")
    console.print("   export ANTHROPIC_API_KEY=your_api_key_here")
    console.print(
        "   export GEMINI_API_KEY=your_api_key_here  # Get from https://aistudio.google.com/app/apikey"
    )
    console.print("\n2. Install required providers:")
    console.print("   pip install dot-context[openai]")
    console.print("   pip install dot-context[anthropic]")
    console.print("   pip install dot-context[gemini]  # Uses OpenAI compatibility")
    console.print("   # Or install all providers with:")
    console.print("   pip install dot-context[all]")


@app.command()
def config(
    config_path: Optional[Path] = typer.Option(
        None, "--file", "-f", help="Path to .context file"
    )
):
    """Display the current configuration."""
    try:
        # If no config path provided, search for one
        if config_path is None:
            found_path = find_config_file()
            if found_path:
                config_path = found_path
                console.print(f"Using config file: [bold]{config_path}[/bold]")
            else:
                console.print("[yellow]No .context file found.[/yellow]")
                console.print("Run [bold]dcx init[/bold] to create one.")
                return

        # Load and display the configuration
        config_data = load_config(config_path)

        # Display Sets
        if "Sets" in config_data and config_data["Sets"]:
            console.print("\n[bold]Context Sets:[/bold]")
            sets_table = Table(show_header=True)
            sets_table.add_column("Name")
            sets_table.add_column("Description")
            sets_table.add_column("Patterns")

            for set_name, set_info in config_data["Sets"].items():
                description = set_info.get("description", "")
                patterns = ", ".join(set_info.get("match", []))
                sets_table.add_row(set_name, description, patterns)

            console.print(sets_table)
        else:
            console.print("\n[yellow]No context sets defined.[/yellow]")

        # Display Models
        if "Models" in config_data and config_data["Models"]:
            console.print("\n[bold]Models:[/bold]")
            models_table = Table(show_header=True)
            models_table.add_column("Name")
            models_table.add_column("Provider")
            models_table.add_column("Model")
            models_table.add_column("Description")

            for model_name, model_info in config_data["Models"].items():
                provider = model_info.get("provider", "")
                model = model_info.get("model", "")
                description = model_info.get("description", "")
                models_table.add_row(model_name, provider, model, description)

            console.print(models_table)
        else:
            console.print("\n[yellow]No models defined.[/yellow]")

    except FileNotFoundError:
        console.print(
            f"[red]Error:[/red] Could not find .context file at {config_path}"
        )
        console.print("Run [bold]dcx init[/bold] to create one.")
    except Exception as e:
        console.print(f"[red]Error loading configuration:[/red] {str(e)}")


# Create a sub-command group for sets
sets_app = typer.Typer(help="Manage context sets")
app.add_typer(sets_app, name="sets")


@sets_app.command("list")
def list_sets(
    config_path: Optional[Path] = typer.Option(
        None, "--file", "-f", help="Path to .context file"
    )
):
    """List all available context sets."""
    try:
        if config_path is None:
            found_path = find_config_file()
            if found_path:
                config_path = found_path
                console.print(f"Using config file: [bold]{config_path}[/bold]")
            else:
                console.print("[yellow]No .context file found.[/yellow]")
                console.print("Run [bold]dcx init[/bold] to create one.")
                return

        context_sets = load_context_sets(config_path)

        if not context_sets:
            console.print("[yellow]No context sets defined.[/yellow]")
            console.print("Edit your .context file to add some sets.")
            return

        console.print("\n[bold]Available Context Sets:[/bold]")
        table = Table(show_header=True)
        table.add_column("Name")
        table.add_column("Description")
        table.add_column("Patterns")
        table.add_column("Includes")

        for name, ctx_set in context_sets.items():
            patterns = ", ".join(ctx_set.match_patterns)
            includes = ", ".join(ctx_set.includes) if ctx_set.includes else ""
            table.add_row(name, ctx_set.description, patterns, includes)

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error listing sets:[/red] {str(e)}")


@sets_app.command("show")
def show_set(
    set_name: str = typer.Argument(..., help="Name of the context set to show"),
    config_path: Optional[Path] = typer.Option(
        None, "--file", "-f", help="Path to .context file"
    ),
):
    """Show files in a specific context set."""
    try:
        if config_path is None:
            found_path = find_config_file()
            if found_path:
                config_path = found_path
                console.print(f"Using config file: [bold]{config_path}[/bold]")
            else:
                console.print("[yellow]No .context file found.[/yellow]")
                console.print("Run [bold]dcx init[/bold] to create one.")
                return

        try:
            files = get_context_set_files(set_name, config_path)

            console.print(
                f"\n[bold]Files in context set '[cyan]{set_name}[/cyan]':[/bold]"
            )

            if not files:
                console.print(
                    "[yellow]No files found matching the patterns in this set.[/yellow]"
                )
                return

            table = Table(show_header=True)
            table.add_column("File", style="cyan")
            table.add_column("Size (bytes)", justify="right")
            table.add_column("Est. Tokens", justify="right")

            total_size = 0
            total_tokens = 0

            for file_path in files:
                # Get token count and size
                file_info = count_tokens_in_file(file_path)
                size = file_info["size_bytes"]
                tokens = file_info["tokens"]

                # Update totals
                total_size += size
                total_tokens += tokens

                # Format token count
                formatted_tokens = format_token_count(tokens)

                table.add_row(str(file_path), str(size), formatted_tokens)

            console.print(table)

            # Print totals
            console.print(
                f"\nTotal: [bold]{len(files)}[/bold] files, "
                f"[bold]{total_size}[/bold] bytes, "
                f"[bold]{format_token_count(total_tokens)}[/bold] estimated tokens"
            )

            # Print context window warning if appropriate
            if total_tokens > 128000:  # Example threshold for Claude
                console.print(
                    "[yellow]Warning:[/yellow] Estimated token count exceeds 128K tokens "
                    "(Claude's context window limit)"
                )

            # Add note about token estimation
            console.print(
                "\n[dim]Note: Token counts are estimates and may vary by model.[/dim]"
            )

        except KeyError:
            console.print(f"[red]Error:[/red] Context set '{set_name}' not found")

    except Exception as e:
        console.print(f"[red]Error showing set:[/red] {str(e)}")


# Create a models sub-command group
models_app = typer.Typer(help="Manage LLM models")
app.add_typer(models_app, name="models")


@models_app.command("list")
def list_models(
    config_path: Optional[Path] = typer.Option(
        None, "--file", "-f", help="Path to .context file"
    )
):
    """List all available models."""
    try:
        if config_path is None:
            found_path = find_config_file()
            if found_path:
                config_path = found_path
                console.print(f"Using config file: [bold]{config_path}[/bold]")
            else:
                console.print("[yellow]No .context file found.[/yellow]")
                console.print("Run [bold]dcx init[/bold] to create one.")
                return

        config_data = load_config(config_path)
        models = config_data.get("Models", {})

        if not models:
            console.print("[yellow]No models defined.[/yellow]")
            console.print("Edit your .context file to add some models.")
            return

        console.print("\n[bold]Available Models:[/bold]")
        table = Table(show_header=True)
        table.add_column("Name")
        table.add_column("Provider")
        table.add_column("Model")
        table.add_column("Description")

        for name, model_info in models.items():
            provider = model_info.get("provider", "")
            model = model_info.get("model", "")
            description = model_info.get("description", "")
            table.add_row(name, provider, model, description)

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error listing models:[/red] {str(e)}")


@app.command()
def query(
    query_text: str = typer.Argument(..., help="The query text to send to the LLM"),
    set_name: str = typer.Option(
        ..., "--set", "-s", help="Name of the context set to use"
    ),
    model_name: str = typer.Option(
        ..., "--model", "-m", help="Name of the model to use"
    ),
    system_prompt: Optional[str] = typer.Option(
        None, "--system", help="Optional system prompt or instructions"
    ),
    temperature: float = typer.Option(
        0.7, "--temperature", "-t", min=0.0, max=2.0, help="Model temperature"
    ),
    max_tokens: Optional[int] = typer.Option(
        None, "--max-tokens", help="Maximum tokens to generate"
    ),
    no_stream: bool = typer.Option(
        False, "--no-stream", help="Disable streaming (wait for full response)"
    ),
    hide_filenames: bool = typer.Option(
        False, "--hide-filenames", help="Exclude filenames from context"
    ),
    config_path: Optional[Path] = typer.Option(
        None, "--file", "-f", help="Path to .context file"
    ),
):
    """
    Query an LLM with a specific context set.
    """
    # Execute the query
    execute_query(
        query=query_text,
        set_name=set_name,
        model_name=model_name,
        system_prompt=system_prompt,
        temperature=temperature,
        max_tokens=max_tokens,
        stream=not no_stream,
        include_filenames=not hide_filenames,
        config_path=config_path,
    )


if __name__ == "__main__":
    app()
