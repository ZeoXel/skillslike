"""FastAPI application for the SkillsLike agent."""

import logging
import os
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from skillslike.agent.core import create_agent, invoke_agent
from skillslike.api.schemas import ChatRequest, ChatResponse, FileMetadata, HealthResponse
from skillslike.config import get_settings
from skillslike.registry import SkillRegistry
from skillslike.router import IntentRouter
from skillslike.storage import FileStore

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="SkillsLike Agent API",
    description="Agent architecture for skill-like progressive loading",
    version="0.1.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
registry: SkillRegistry | None = None
router: IntentRouter | None = None
file_store: FileStore | None = None


# Mount static files
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except RuntimeError:
    # Static directory doesn't exist, skip mounting
    pass


@app.on_event("startup")
async def startup_event() -> None:
    """Initialize application on startup."""
    global registry, router, file_store

    # Get configuration from environment
    skills_dir = os.getenv("SKILLS_DIR", "skills/")
    file_store_dir = os.getenv("FILE_STORE_DIR", "data/files/")

    logger.info("Initializing SkillsLike Agent API")

    # Initialize file store
    file_store = FileStore(file_store_dir)

    # Initialize registry
    try:
        registry = SkillRegistry(skills_dir)
        logger.info("Loaded %d skills", len(registry.manifests))
    except ValueError as e:
        logger.warning("Failed to load skills: %s", e)
        # Create empty registry with fallback
        Path(skills_dir).mkdir(parents=True, exist_ok=True)
        registry = SkillRegistry(skills_dir)

    # Initialize router
    manifests = registry.get_all_manifests()
    router = IntentRouter(manifests, max_tools=5)

    logger.info("Application startup complete")


@app.get("/", include_in_schema=False)
async def root() -> FileResponse:
    """Serve the frontend application."""
    return FileResponse("static/index.html")


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint.

    Returns:
        Health status and loaded skills count.
    """
    skills_loaded = len(registry.manifests) if registry else 0
    return HealthResponse(status="healthy", skills_loaded=skills_loaded)


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """Chat with the agent.

    Args:
        request: Chat request with message and optional thread_id.

    Returns:
        Agent response with text, files, and thread_id.

    Raises:
        HTTPException: If agent execution fails.
    """
    if not registry or not router:
        raise HTTPException(status_code=500, detail="Agent not initialized")

    # Generate thread_id if not provided
    thread_id = request.thread_id or uuid4().hex

    logger.info("Chat request on thread %s: %s", thread_id, request.message[:50])

    try:
        # Get all tools
        all_tools = registry.get_all_tools()

        # Route to relevant tools
        selected_tools = router.route_tools(
            request.message,
            all_tools,
            get_manifest=registry.get_manifest,
        )

        logger.info("Selected %d tools for this request", len(selected_tools))

        # Get settings for API configuration
        settings = get_settings()

        # Determine which API to use
        base_url = None
        api_key = None

        if settings.use_openai_compatible and settings.openai_base_url:
            # Use OpenAI-compatible endpoint
            base_url = settings.openai_base_url
            api_key = settings.openai_api_key
            logger.info("Using OpenAI-compatible API: %s", base_url)
        elif settings.anthropic_base_url:
            # Use custom Anthropic endpoint
            base_url = settings.anthropic_base_url
            api_key = settings.anthropic_api_key
            logger.info("Using custom Anthropic API: %s", base_url)

        # Create agent with selected tools and custom API config
        agent = create_agent(selected_tools, base_url=base_url, api_key=api_key)

        # Invoke agent
        result = invoke_agent(agent, request.message, thread_id=thread_id)

        # Return response
        return ChatResponse(
            text=result["text"],
            files=result.get("file_ids", []),
            thread_id=thread_id,
        )

    except Exception as e:
        logger.error("Agent execution failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {e}") from e


@app.get("/api/file/{file_id}", response_class=StreamingResponse)
async def download_file(file_id: str) -> StreamingResponse:
    """Download a file by ID.

    Args:
        file_id: The file ID.

    Returns:
        File content.

    Raises:
        HTTPException: If file not found.
    """
    if not file_store:
        raise HTTPException(status_code=500, detail="File store not initialized")

    # Get file content
    content = file_store.retrieve(file_id)

    if content is None:
        raise HTTPException(status_code=404, detail="File not found")

    # Get metadata
    metadata = file_store.get_metadata(file_id)

    filename = metadata.get("filename", file_id) if metadata else file_id
    content_type = metadata.get("content_type", "application/octet-stream") if metadata else "application/octet-stream"

    logger.info("Serving file: %s", filename)

    # Return file as streaming response
    from io import BytesIO

    return StreamingResponse(
        BytesIO(content),
        media_type=content_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/api/file/{file_id}/metadata", response_model=FileMetadata)
async def get_file_metadata(file_id: str) -> FileMetadata:
    """Get file metadata by ID.

    Args:
        file_id: The file ID.

    Returns:
        File metadata.

    Raises:
        HTTPException: If file not found.
    """
    if not file_store:
        raise HTTPException(status_code=500, detail="File store not initialized")

    metadata = file_store.get_metadata(file_id)

    if metadata is None:
        raise HTTPException(status_code=404, detail="File not found")

    return FileMetadata(**metadata)


@app.get("/api/skills")
async def list_skills() -> list[dict[str, str]]:
    """List all loaded skills.

    Returns:
        List of skill metadata.
    """
    if not registry:
        raise HTTPException(status_code=500, detail="Registry not initialized")

    manifests = registry.get_all_manifests()

    return [
        {
            "name": m.name,
            "description": m.description,
            "runtime": m.runtime.type,
            "tags": ", ".join(m.tags),
        }
        for m in manifests
    ]


@app.post("/api/reload")
async def reload_skills() -> dict[str, str]:
    """Reload skills from disk.

    Returns:
        Status message.
    """
    if not registry:
        raise HTTPException(status_code=500, detail="Registry not initialized")

    registry.reload()

    # Update router with new manifests
    global router
    manifests = registry.get_all_manifests()
    router = IntentRouter(manifests, max_tools=5)

    logger.info("Skills reloaded: %d manifests", len(manifests))

    return {"status": "success", "skills_loaded": len(manifests)}


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("API_PORT", "8000"))
    host = os.getenv("API_HOST", "0.0.0.0")

    uvicorn.run(app, host=host, port=port)
