"""Pydantic schemas for API requests and responses."""

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request schema for chat endpoint."""

    message: str = Field(description="User message")
    thread_id: str | None = Field(default=None, description="Optional thread ID for context")


class ChatResponse(BaseModel):
    """Response schema for chat endpoint."""

    text: str = Field(description="Agent response text")
    files: list[str] = Field(default_factory=list, description="List of file IDs")
    thread_id: str = Field(description="Thread ID for context continuity")


class FileMetadata(BaseModel):
    """File metadata schema."""

    file_id: str
    filename: str
    content_type: str


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "healthy"
    skills_loaded: int = 0
