# Quick Start Guide

This guide will help you get started with SkillsLike in minutes.

## Installation

```bash
cd skillslike
uv sync
```

## Environment Setup

1. Copy the example environment file:

```bash
cp .env.example .env
```

2. Edit `.env` and add your Anthropic API key:

```bash
ANTHROPIC_API_KEY=your-api-key-here
```

## Basic Usage

### Option 1: Python API

```python
from skillslike.agent.core import create_agent, invoke_agent
from skillslike.registry import SkillRegistry
from skillslike.router import IntentRouter

# Load skills
registry = SkillRegistry("skills/")
router = IntentRouter(registry.get_all_manifests())

# Get tools
all_tools = registry.get_all_tools()
selected_tools = router.route_tools("Analyze Excel data", all_tools)

# Create and run agent
agent = create_agent(selected_tools)
result = invoke_agent(agent, "Analyze this spreadsheet", thread_id="session-1")

print(result["text"])
```

### Option 2: FastAPI Server

1. Start the server:

```bash
make run
# or
uvicorn skillslike.api.main:app --reload
```

2. Use the API:

```bash
# Health check
curl http://localhost:8000/health

# List skills
curl http://localhost:8000/api/skills

# Chat
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Summarize this document", "thread_id": "session-1"}'
```

## Creating a Custom Skill

1. Create a manifest file in `skills/`:

```yaml
name: my-custom-skill
description: Does something useful. Triggers on keywords like custom, special
inputs:
  - type: text
    description: User instructions
outputs:
  - type: text
    description: Result
runtime:
  type: service
  endpoint: http://localhost:8001/my-skill
  timeout: 60
tags:
  - custom
  - example
```

2. Reload skills:

```bash
curl -X POST http://localhost:8000/api/reload
```

## Running Tests

```bash
make test
```

## Next Steps

- Read the [Architecture](architecture.md) document for design details
- Check out example skills in `skills/examples/`
- Explore the API documentation at `http://localhost:8000/docs` (when server is running)
- Implement custom executors for your specific needs

## Troubleshooting

### No skills loaded

- Make sure you have manifest files in the `skills/` directory
- Check the logs for validation errors
- Ensure your YAML syntax is correct

### API errors

- Verify your `ANTHROPIC_API_KEY` is set correctly
- Check that the API server is running on the correct port
- Review the server logs for detailed error messages

### Tests failing

- Ensure all dependencies are installed: `uv sync`
- Check Python version (requires 3.11+)
- Run with verbose output: `pytest -vv`
