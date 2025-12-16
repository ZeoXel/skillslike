# SkillsLike

Agent architecture for skill-like progressive loading using LangChain + LangGraph.

## Overview

This project replicates Claude Skills behaviors when custom skill upload is unavailable. It provides:

- **Modular Skills**: YAML-based skill manifests with runtime definitions
- **Progressive Loading**: Intent-aware routing loads only relevant tools
- **Containerized Execution**: Docker/K8s backed execution sandbox
- **Persistent Context**: Thread-based checkpointing for multi-turn conversations
- **Clean API**: FastAPI endpoints for web clients

## Architecture

See [docs/architecture.md](docs/architecture.md) for detailed design.

### Components

- **Skill Manifest**: YAML definitions for each skill
- **Tool Registry**: Loads manifests and builds LangChain tools
- **Intent Router**: Keyword-based routing to filter tools
- **Agent Core**: LangGraph loop with checkpointing
- **Execution Sandbox**: Docker/service executor for custom logic
- **API Layer**: FastAPI endpoints (`/api/chat`, `/api/file`)

## Installation

```bash
# Install with uv
uv sync

# Or with pip
pip install -e .
```

## Quick Start

```bash
# Set environment variables
cp .env.example .env
# Edit .env with your API keys

# Run the API server
uvicorn skillslike.api.main:app --reload
```

## Usage

```python
from skillslike.agent import create_agent
from skillslike.registry import SkillRegistry

# Load skills
registry = SkillRegistry("skills/")
tools = registry.get_all_tools()

# Create agent
agent = create_agent(tools_subset=tools)

# Run agent
result = agent.invoke(
    {"messages": [{"role": "user", "content": "Summarize this document"}]},
    config={"configurable": {"thread_id": "session-123"}}
)
```

## Development

```bash
# Run tests
pytest

# Lint
ruff check .

# Format
ruff format .

# Type check
mypy .
```

## Project Structure

```
skillslike/
├── skillslike/          # Core package
│   ├── models/          # Pydantic schemas
│   ├── registry/        # Tool loading and registry
│   ├── router/          # Intent routing
│   ├── agent/           # LangGraph agent core
│   ├── executors/       # Tool executors
│   ├── storage/         # File and state storage
│   └── api/             # FastAPI endpoints
├── skills/              # Skill manifests
├── tests/               # Test suite
└── docs/                # Documentation
```

## License

MIT
# skillslike
