# Agent Architecture for Skill-Like Progressive Loading

Use LangChain + LangGraph to replicate Claude Skills behaviors when custom skill upload is unavailable. Goals: modular “skills”, intent-aware progressive loading, containerized code execution, persistent context, and a small API surface for web clients.

## Key LangChain/LangGraph Concepts (v1+)
- **Tool / StructuredTool**: wraps any external API (your gateway endpoints) with schema + description; better routing and validation.
- **Router / Conditional edges**: select a subset of tools/models based on intent; mimics “lazy loading” of skills.
- **Agent loop with LangGraph**: `llm_call -> tool_node -> llm_call` using `StateGraph`; checkpoints give container-like context reuse via `thread_id`.
- **Structured output**: `with_structured_output` for plans/args; `bind_tools` for function calling.
- **Checkpointer**: MemorySaver for dev; Redis/DB in prod; thread-scoped state keeps multi-turn continuity.

## Component Overview
- **Skill manifest**: YAML/JSON per skill. Fields: `name`, `description` (trigger hints), `inputs`, `outputs`, `runtime` (docker image or service endpoint), `requires` (secrets/volumes), `tags`.
- **Tool registry**: Load manifests → build `StructuredTool`/`Tool`; store in registry.
- **Intent router**: Keyword/rule/classifier to pick candidate tools from registry; only bind this subset to the agent (progressive load).
- **Agent core**: LangGraph loop with conditional edges; uses a chosen LLM (via your gateway) + the filtered tools.
- **Execution sandbox**: For custom logic, call your internal executor (Docker/K8s/Serverless). For official Anthropic skills, call the proxy API.
- **State & files**: Checkpointed state keyed by `thread_id`; file store (S3/minio/local). Tool outputs return text + `file_id`/task id.
- **API layer**: FastAPI `/api/chat`, `/api/file/{id}`, `/api/context/{thread_id}`; front-end only talks to these.

## Skill Manifest (example)
```yaml
name: knowledge-reorganizer
description: reorganize and summarize documents; triggers on "重组", "梳理", "总结"
inputs:
  - type: file
    formats: [pdf, docx, txt]
runtime:
  type: docker
  image: your-registry/reorganizer:latest
  cmd: ["python", "main.py"]
outputs:
  - type: file
    format: docx
tags: [summarization, restructure]
```

## Registry and Router (Python sketch)
```python
# load manifests -> tools
manifests = load_manifests("skills/")  # returns list[SkillMeta]
tools = [build_tool_from_manifest(m) for m in manifests]  # StructuredTool preferred

def route_tools(user_msg: str) -> list:
    # simple heuristic or classifier; use embeddings later if needed
    return [t for t in tools if keyword_match(user_msg, t.description)]
```

## Agent Core with LangGraph
```python
from langchain.agents import create_agent
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

def build_agent(tools_subset):
    agent = create_agent(
        model="anthropic:claude-3-5-sonnet-latest",  # or your provider
        tools=tools_subset,
        system_prompt="Concise. Use tools when helpful. Maintain thread context."
    )
    # Graph loop
    def llm_call(state): return {"messages": agent.invoke({"messages": state["messages"]})["messages"]}
    def tool_node(state): return run_tool_calls(state["messages"][-1], tools_subset)
    def should_continue(state): return "tool_node" if state["messages"][-1].tool_calls else END

    sg = StateGraph(dict)
    sg.add_node("llm_call", llm_call)
    sg.add_node("tool_node", tool_node)
    sg.add_edge(START, "llm_call")
    sg.add_conditional_edges("llm_call", should_continue, ["tool_node", END])
    sg.add_edge("tool_node", "llm_call")
    return sg.compile(checkpointer=MemorySaver())
```

## Tool Shape
- **Official Anthropic skills**: Tool wraps the proxy `/v1/messages` call with `container.skills=[{type:"anthropic",skill_id:...}]`; parse text and file outputs.
- **Custom logic**: Tool calls your executor (Docker/K8s/Serverless) via HTTP/RPC; returns summary text + `file_id` from your store; enforce timeouts/retries/errors.

## Tool Shape
- For official Anthropic skills: Tool wraps a call to the proxy API (`/v1/messages` with `container.skills=[{type:"anthropic",skill_id:...}]`). Return text plus file ids if present.
- For custom logic: Tool sends payload to your executor (Docker job or service). Return a `ToolMessage` with summary text and file ids stored in your file store.
- Each tool must be idempotent and time-limited; include retries and structured errors.

## API Surface (FastAPI sketch)
```python
@app.post("/api/chat")
async def chat(req: ChatRequest):
    thread_id = req.thread_id or uuid4().hex
    tools_subset = route_tools(req.message)
    graph = build_agent(tools_subset)
    result = graph.invoke({"messages": [{"role": "user", "content": req.message}]},
                          config={"configurable": {"thread_id": thread_id}})
    text = collect_text(result["messages"])
    files = collect_file_ids(result["messages"])
    return {"text": text, "files": files, "thread_id": thread_id}

@app.get("/api/file/{file_id}")
async def download(file_id: str): return stream_from_store(file_id)
```

## Context Persistence
- Use LangGraph checkpointer (MemorySaver for dev; Redis/DB for prod) keyed by `thread_id`.
- Store both messages and tool outputs; rehydrate on each request to maintain long-running context, similar to Claude container reuse.

## Observability and Safety
- Log every tool call (inputs/outputs/latency). Add timeouts per tool and per executor job.
- Validate manifest: required fields, image allowlist, resource limits.
- Sanitize user inputs before passing to executors; run containers with least privilege.
- Add circuit breakers for failing tools; fall back to LLM-only reply when all tools fail.

## Rollout Plan
1) Wire official Anthropic skills as tools (proxy API). Verify Excel/Docx/PPTX/PDF flows end-to-end.
2) Implement manifest loader + router + LangGraph loop with checkpointing.
3) Add custom executor-backed tools (Docker/K8s). Return file ids from your store.
4) Harden: timeouts, retries, metrics, audit logs, input validation.
5) Add LangSmith or your tracing to debug trajectories and tool choices.
6) Expose the FastAPI endpoints to the web client; keep the interface stable (`text`, `files`, `thread_id`).

## Notes
- Keep tools minimal and composable; avoid a “god tool.”
- Prefer StructuredTool with Pydantic schemas for clearer args and better routing.
- Start with keyword routing, upgrade to embedding or classifier-based routing as skills grow.
- Maintain a manifest registry in git; CI validates manifests and can spin up ephemeral containers for smoke tests.
