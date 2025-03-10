# Dot Context (dcx)
A CLI tool for configurable LLM context management and queries

## Overview
Dot Context allows configuration of LLM context and queries. 

> **⚠️ Work in Progress**  
> This tool is currently under active development and is not yet published to PyPI.

## Installation

Since this package is not yet published to PyPI, you'll need to install it from the local directory:

```bash
# Clone the repository
git clone https://github.com/username/dot-context.git
cd dot-context

# Install in development mode
pip install -e .
```

### Quick Start

Initialize a `.context` file in your project:

```bash
dcx init
```

Edit the generated `.context` file to define your context sets and models. 

Sets use glob patterns to determine which files will be pulled in as context for the query, while models define which options you have (o1, gemini, etc). 

```yaml
Sets:
  worldbuilding:
    match:
      - "world/**/*.md"
    description: "World lore and settings"
  
  characters:
    match:
      - "characters/**/*.md"
    description: "Character profiles"

Models:
  large-context:
    provider: gemini
    api-key: ${GEMINI_API_KEY}
    model: gemini-2.0-flash
    description: "Gemini model"
  
  quick-questions:
    provider: openai
    api-key: ${OPENAI_API_KEY}
    model: gpt-4o
    description: "OpenAI GPT-4o model"
```

Set your API keys as environment variables:

```bash
export ANTHROPIC_API_KEY=your_api_key_here
export OPENAI_API_KEY=your_api_key_here
export GEMINI_API_KEY=your_api_key_here
```

Query an LLM with a specific context:

```bash
dcx query --set worldbuilding --model quick-questions "Describe the climate of the Northern Region"
```

## Context Sets

List all available context sets:

```bash
dcx sets list
```

Show files in a specific context set:

```bash
dcx sets show worldbuilding
```

## Models

List all available models:

```bash
dcx models list
```

## Querying

Query an LLM with a specific context set:

```bash
dcx query --set  --model  "Your query text here"
```

### Using Multiple Context Sets

You can combine multiple context sets in a single query by using a comma-separated list:

```bash
dcx query --set code,tests --model openai "How well is the test coverage for this project?"
```

This will include all files from both the "code" and "tests" sets, removing any duplicates.

### Query Options

- `--set, -s TEXT`: Name of context set(s) to use (comma-separated for multiple sets)
- `--model, -m TEXT`: Name of the model to use
- `--system TEXT`: Provide a system prompt or instructions
- `--temperature, -t FLOAT`: Set the temperature (creativity) parameter (default: 0.7)
- `--max-tokens INTEGER`: Maximum number of tokens to generate
- `--no-stream`: Disable streaming (wait for full response)
- `--hide-filenames`: Exclude filenames from context
- `--no-history`: Don't save the query to history

## Configuration
The .context file supports:

- File matching with glob patterns
- Set composition by including other sets
- Multiple models from different providers
- Environment variables for sensitive keys

## History

The dot-context tool keeps a history of your queries and their results. You can view and manage this history with the following commands:

### View Recent Queries

List your most recent queries:

```bash
dcx history
```

By default, this shows the 5 most recent queries. You can adjust this with the `--max` option:

```bash
dcx history --max 10
```

### View Details of a Query

View the full details of a specific query using its ID:

```bash
dcx history <ID>
```

### Save a Query Result

Save a query result to a file:

```bash
dcx history <ID> --save result.md
```

The file format is determined by the extension:
- `.json`: Saves the full entry with metadata
- `.md`: Saves a formatted Markdown document
- `.txt`: Saves a plain text version

### Disabling History

If you don't want to save a query to history, use the `--no-history` flag:

```bash
dcx query --set worldbuilding --model gpt4 --no-history "Your query here"
```

## Current Status

This tool is in active development. Some features may be incomplete or subject to change.

## License

MIT License