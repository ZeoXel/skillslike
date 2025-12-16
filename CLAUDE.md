# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SkillsLike is an agent architecture that replicates Claude Skills behaviors using LangChain + LangGraph. It provides modular, YAML-based skill definitions with progressive loading, containerized execution, and persistent context management.

**Core Technology Stack:**
- LangChain/LangGraph for agent orchestration
- FastAPI for REST API
- Anthropic Claude for LLM
- Python 3.11+ with uv package manager
- Docker for containerization

## Development Commands

### Package Management
```bash
# Install dependencies (use uv, not npm/pip)
uv sync

# Install with dev dependencies
uv sync --group dev
```

### Running the Application
```bash
# Start the API server (development)
uvicorn skillslike.api.main:app --reload

# Or using uv
uv run uvicorn skillslike.api.main:app --reload

# Production (via Docker)
docker build -t skillslike .
docker run -p 8000:8000 --env-file .env skillslike
```

### Testing and Quality
```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=skillslike --cov-report=term-missing

# Run specific test file
pytest tests/unit_tests/test_router.py

# Linting
ruff check .

# Format code
ruff format .

# Type checking
mypy .
```

## Architecture Overview

### Core Components Flow
1. **Skill Manifest** (YAML) → defines skill metadata, triggers, I/O, and runtime
2. **Tool Registry** → loads manifests and builds LangChain StructuredTools
3. **Intent Router** → keyword-based routing filters tools for each request
4. **Agent Core** → LangGraph StateGraph with checkpointing for multi-turn conversations
5. **Executors** → runtime handlers (Anthropic API, custom services, image generation)
6. **API Layer** → FastAPI endpoints exposing `/api/chat`, `/api/file`, `/api/skills`

### Key Design Patterns

**Progressive Tool Loading:**
- Not all tools are loaded for every request
- `IntentRouter` (router/intent_router.py) analyzes user message and selects relevant tools
- Reduces token usage and improves response time

**Stateful Conversations:**
- LangGraph checkpointer (MemorySaver) maintains state per `thread_id`
- Each conversation thread persists messages and tool outputs
- Agent can reference previous context in multi-turn interactions

**Executor Pattern:**
- Base executor interface in `executors/base.py`
- Specialized executors:
  - `AnthropicExecutor`: calls official Anthropic skills API
  - `CustomExecutor`: invokes Docker/service-based custom logic
  - `ImageGenExecutor`: handles image generation via nano-banana-2 API
- Executors are selected in `registry.py:build_tool()` based on manifest runtime type

### File Storage
- `FileStore` (storage/file_store.py) manages generated files
- Files stored with metadata (filename, content_type, created_at)
- File IDs extracted from tool outputs and returned in API responses
- On serverless platforms (Vercel), uses `/tmp/files/` to avoid read-only filesystem issues

## Environment Configuration

Required environment variables (`.env` file):
```bash
# Anthropic API (required)
ANTHROPIC_API_KEY=sk-ant-...

# Optional: use custom/third-party Anthropic-compatible endpoint
ANTHROPIC_BASE_URL=https://your-proxy.com/v1

# Optional: OpenAI-compatible provider
USE_OPENAI_COMPATIBLE=false
OPENAI_API_KEY=...
OPENAI_BASE_URL=...

# LangSmith tracing (optional)
LANGCHAIN_TRACING_V2=false
LANGCHAIN_API_KEY=...
LANGCHAIN_PROJECT=skillslike

# Application settings
SKILLS_DIR=skills/
FILE_STORE_DIR=data/files/
```

## Adding New Skills

Create a YAML manifest in `skills/` directory:

```yaml
name: my-custom-skill
description: Brief description with trigger keywords like "keyword1", "keyword2"
inputs:
  - type: text
    description: Input parameter description
outputs:
  - type: file
    format: png
runtime:
  type: service  # or "docker" or "anthropic"
  endpoint: https://api.example.com/v1/endpoint
  timeout: 60
tags:
  - category-name
metadata:
  version: "1.0.0"
  provider: provider-name
```

**Runtime Types:**
- `anthropic`: Use official Anthropic skills proxy
- `service`: HTTP endpoint executor
- `docker`: Container-based executor (requires Docker enabled)

**Tool Selection Logic:**
Skills are selected based on keyword matching between user message and manifest `description` field. Include relevant trigger words in the description.

## Project Structure Highlights

```
skillslike/
├── skillslike/
│   ├── agent/           # LangGraph agent loop
│   │   ├── core.py      # create_agent(), invoke_agent()
│   │   └── state.py     # AgentState TypedDict
│   ├── api/             # FastAPI endpoints
│   │   ├── main.py      # App initialization, /api/chat, /api/file
│   │   └── schemas.py   # Pydantic request/response models
│   ├── executors/       # Tool execution backends
│   │   ├── base.py      # BaseExecutor interface
│   │   ├── anthropic_executor.py
│   │   ├── custom_executor.py
│   │   └── image_gen_executor.py
│   ├── models/          # Data models
│   │   └── manifest.py  # SkillManifest Pydantic model
│   ├── registry/        # Skill and tool management
│   │   ├── loader.py    # Load YAML manifests
│   │   └── registry.py  # SkillRegistry, build_tool()
│   ├── router/          # Intent routing
│   │   └── intent_router.py
│   ├── storage/         # File management
│   │   └── file_store.py
│   └── config.py        # Settings management
├── skills/              # Skill manifest YAML files
├── tests/               # Test suite
│   └── unit_tests/
├── docs/                # Architecture documentation
└── static/              # Frontend assets (if present)
```

## Important Implementation Notes

### Agent Creation (agent/core.py)
- `create_agent()` returns a compiled StateGraph, not a callable agent
- Must call `invoke_agent()` or `app.invoke()` directly
- System prompt injected on first message only
- Tools bound via `model.bind_tools(tools_subset)`

### API Configuration
The API supports multiple LLM providers:
- Default: Anthropic API (via `ANTHROPIC_API_KEY`)
- Custom Anthropic proxy: Set `ANTHROPIC_BASE_URL`
- OpenAI-compatible providers: Set `USE_OPENAI_COMPATIBLE=true` and `OPENAI_BASE_URL`

Configuration logic in `api/main.py:chat()` selects provider based on settings.

### File ID Extraction
Tool outputs can include file IDs in format: `file_id: <id>`
The `process_tool_output` node in agent graph extracts these and adds to state.

### Checkpointing
- Development: `MemorySaver` (in-memory, lost on restart)
- Production: Switch to Redis or SQLite checkpointer for persistence
- Thread ID is required for all requests to maintain conversation continuity

## Deployment

### Docker
```bash
# Build image
docker build -t skillslike .

# Run container
docker run -p 8000:8000 --env-file .env skillslike
```

### Vercel (Serverless)
- `vercel.json` configured for deployment
- Uses `/tmp/files/` for file storage (ephemeral)
- No Docker executor support in serverless mode

## Debugging and Observability

### Logging
- All modules use Python `logging` with INFO level by default
- Key log points:
  - Tool selection: `router.py`
  - Agent invocation: `core.py`
  - API requests: `main.py`

### LangSmith Integration
Enable tracing by setting environment variables:
```bash
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=<your-key>
LANGCHAIN_PROJECT=skillslike
```

### Common Issues

**Skill not loaded:**
- Check YAML syntax in manifest file
- Verify file is in `SKILLS_DIR` (default: `skills/`)
- Check logs for validation warnings

**Tool not selected:**
- Intent router uses keyword matching on manifest `description`
- Add more trigger keywords to skill description
- Check router logs for selected tool count

**File storage issues:**
- Verify `FILE_STORE_DIR` directory exists and is writable
- On Vercel, files are ephemeral (stored in `/tmp/`)

## Code Style and Conventions

- Python 3.11+ type hints required (`mypy` strict mode)
- Line length: 100 characters (ruff)
- Use `StructuredTool` with Pydantic schemas for better type safety
- All async functions use `async def` even if not strictly required
- Import order: stdlib → third-party → local (enforced by ruff)
