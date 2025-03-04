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

# For OpenAI support:
pip install -e ".[openai]"

# For Anthropic support:
pip install -e ".[anthropic]"

# For all providers:
pip install -e ".[all]"
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
dcx query --set <set_name> --model <model_name> "Your query text here"
```

### Query Options

- `--system TEXT`: Provide a system prompt or instructions
- `--temperature FLOAT`: Set the temperature (creativity) parameter (default: 0.7)
- `--max-tokens INTEGER`: Maximum number of tokens to generate
- `--no-stream`: Disable streaming (wait for full response)
- `--hide-filenames`: Exclude filenames from context

## Configuration
The .context file supports:

- File matching with glob patterns
- Set composition by including other sets
- Multiple models from different providers
- Environment variables for sensitive keys

## Current Status

This tool is in active development. Some features may be incomplete or subject to change.

## License

MIT License
