"""Unit tests for manifest models."""

import pytest
from pydantic import ValidationError

from skillslike.models.manifest import (
    InputSpec,
    InputType,
    OutputSpec,
    OutputType,
    RuntimeConfig,
    RuntimeType,
    SkillManifest,
)


def test_input_spec_creation() -> None:
    """Test creating an InputSpec."""
    spec = InputSpec(type=InputType.FILE, formats=["pdf", "docx"])

    assert spec.type == InputType.FILE
    assert spec.formats == ["pdf", "docx"]


def test_output_spec_creation() -> None:
    """Test creating an OutputSpec."""
    spec = OutputSpec(type=OutputType.FILE, format="xlsx")

    assert spec.type == OutputType.FILE
    assert spec.format == "xlsx"


def test_runtime_config_docker() -> None:
    """Test RuntimeConfig for Docker runtime."""
    config = RuntimeConfig(
        type=RuntimeType.DOCKER,
        image="my-image:latest",
        cmd=["python", "main.py"],
        timeout=300,
    )

    assert config.type == RuntimeType.DOCKER
    assert config.image == "my-image:latest"
    assert config.cmd == ["python", "main.py"]
    assert config.timeout == 300


def test_runtime_config_service() -> None:
    """Test RuntimeConfig for service runtime."""
    config = RuntimeConfig(
        type=RuntimeType.SERVICE,
        endpoint="http://localhost:8001/api",
    )

    assert config.type == RuntimeType.SERVICE
    assert config.endpoint == "http://localhost:8001/api"


def test_runtime_config_anthropic() -> None:
    """Test RuntimeConfig for Anthropic runtime."""
    config = RuntimeConfig(
        type=RuntimeType.ANTHROPIC,
        skill_id="excel-skill",
    )

    assert config.type == RuntimeType.ANTHROPIC
    assert config.skill_id == "excel-skill"


def test_skill_manifest_creation() -> None:
    """Test creating a complete SkillManifest."""
    manifest = SkillManifest(
        name="test-skill",
        description="A test skill for testing",
        inputs=[
            InputSpec(type=InputType.FILE, formats=["pdf"]),
            InputSpec(type=InputType.TEXT),
        ],
        outputs=[
            OutputSpec(type=OutputType.FILE, format="docx"),
        ],
        runtime=RuntimeConfig(
            type=RuntimeType.DOCKER,
            image="test:latest",
        ),
        tags=["test", "demo"],
    )

    assert manifest.name == "test-skill"
    assert manifest.description == "A test skill for testing"
    assert len(manifest.inputs) == 2
    assert len(manifest.outputs) == 1
    assert manifest.runtime.type == RuntimeType.DOCKER
    assert "test" in manifest.tags


def test_skill_manifest_validation_missing_name() -> None:
    """Test that SkillManifest requires a name."""
    with pytest.raises(ValidationError):
        SkillManifest(
            description="Missing name",
            runtime=RuntimeConfig(type=RuntimeType.DOCKER, image="test:latest"),
        )


def test_skill_manifest_validation_missing_description() -> None:
    """Test that SkillManifest requires a description."""
    with pytest.raises(ValidationError):
        SkillManifest(
            name="test-skill",
            runtime=RuntimeConfig(type=RuntimeType.DOCKER, image="test:latest"),
        )


def test_skill_manifest_defaults() -> None:
    """Test SkillManifest default values."""
    manifest = SkillManifest(
        name="minimal-skill",
        description="Minimal skill definition",
        runtime=RuntimeConfig(type=RuntimeType.SERVICE, endpoint="http://test"),
    )

    assert manifest.inputs == []
    assert manifest.outputs == []
    assert manifest.requires == []
    assert manifest.tags == []
    assert manifest.metadata == {}
