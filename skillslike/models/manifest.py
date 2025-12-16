"""Pydantic models for skill manifests."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class InputType(str, Enum):
    """Supported input types for skills."""

    FILE = "file"
    TEXT = "text"
    JSON = "json"


class OutputType(str, Enum):
    """Supported output types for skills."""

    FILE = "file"
    TEXT = "text"
    JSON = "json"


class RuntimeType(str, Enum):
    """Supported runtime types for skill execution."""

    DOCKER = "docker"
    SERVICE = "service"
    ANTHROPIC = "anthropic"


class InputSpec(BaseModel):
    """Specification for skill input."""

    type: InputType
    formats: list[str] | None = Field(default=None, description="Allowed file formats")
    description: str | None = Field(default=None, description="Input description")


class OutputSpec(BaseModel):
    """Specification for skill output."""

    type: OutputType
    format: str | None = Field(default=None, description="Output file format")
    description: str | None = Field(default=None, description="Output description")


class RuntimeConfig(BaseModel):
    """Runtime configuration for skill execution."""

    type: RuntimeType
    image: str | None = Field(default=None, description="Docker image for container runtime")
    cmd: list[str] | None = Field(default=None, description="Command to execute")
    endpoint: str | None = Field(
        default=None, description="Service endpoint for service runtime"
    )
    skill_id: str | None = Field(
        default=None, description="Anthropic skill ID for anthropic runtime"
    )
    timeout: int = Field(default=300, description="Execution timeout in seconds")
    env: dict[str, str] = Field(default_factory=dict, description="Environment variables")


class SkillManifest(BaseModel):
    """Complete skill manifest definition.

    Defines a skill's metadata, inputs, outputs, runtime configuration,
    and routing hints for progressive loading.
    """

    name: str = Field(description="Unique skill identifier")
    description: str = Field(
        description="Skill description with trigger keywords for routing"
    )
    inputs: list[InputSpec] = Field(default_factory=list, description="Input specifications")
    outputs: list[OutputSpec] = Field(default_factory=list, description="Output specifications")
    runtime: RuntimeConfig = Field(description="Runtime execution configuration")
    requires: list[str] = Field(
        default_factory=list, description="Required secrets or volumes"
    )
    tags: list[str] = Field(default_factory=list, description="Skill categorization tags")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )

    model_config = {"use_enum_values": True}
