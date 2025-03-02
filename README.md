# Dot Context (dcx)
A CLI tool for configurable LLM context management (Note, this is WIP. If you've somehow stumbled in here, the below is not quite accurate yet.)

## Overview
Dot Context is a simple, powerful command-line tool that helps you manage context for AI large language models. It allows you to define context sets from your project files and query various LLM providers with those contexts.
Perfect for fiction writers, developers, researchers, and anyone who needs consistent context when working with AI models.

## Installation
```bash
pip install dot-context
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
```

Set your API keys as environment variables:

```bash
export ANTHROPIC_API_KEY=your_api_key_here
export OPENAI_API_KEY=your_api_key_here
```

Query an LLM with a specific context:

```bash
dcx query --set worldbuilding --model claude "Describe the climate of the Northern Region"
```

## Configuration
The .context file supports:

File matching with glob patterns
Set composition by including other sets
Multiple models from different providers
Environment variables for sensitive keys
