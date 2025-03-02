# Dot Context (dcx)
A CLI tool for configurable LLM context management and queries

## Overview
Dot Context is a simple, powerful command-line tool that helps you manage context for AI large language models. It allows you to define context sets from your project files and query various LLM providers with those contexts.
Perfect for fiction writers, developers, researchers, and anyone who needs consistent context when working with AI models.

## Installation
```bash
pip install dot-context
```

For OpenAI support:
```bash
pip install dot-context[openai]
```

For all providers:
```bash
pip install dot-context[all]
```

### Quick Start

Initialize a `.context` file in your project:

```bash
dcx init
```

Edit the generated `.context` file to define your context sets and models:

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
  claude:
    provider: anthropic
    api-key: ${ANTHROPIC_API_KEY}
    model: claude-3-opus
    description: "Large context model"
  
  gpt4:
    provider: openai
    api-key: ${OPENAI_API_KEY}
    model: gpt-4
    description: "OpenAI GPT-4 model"
```

Set your API keys as environment variables:

```bash
export ANTHROPIC_API_KEY=your_api_key_here
export OPENAI_API_KEY=your_api_key_here
```

Query an LLM with a specific context:

```bash
dcx query --set worldbuilding --model gpt4 "Describe the climate of the Northern Region"
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