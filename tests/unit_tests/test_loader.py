"""Unit tests for manifest loader."""

import tempfile
from pathlib import Path

import pytest

from skillslike.models.manifest import RuntimeType, SkillManifest
from skillslike.registry.loader import ManifestLoader


@pytest.fixture
def temp_skills_dir() -> Path:
    """Create a temporary directory for test manifests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_manifest(temp_skills_dir: Path) -> Path:
    """Create a sample manifest file."""
    manifest_path = temp_skills_dir / "test-skill.yaml"
    manifest_content = """
name: test-skill
description: A test skill
inputs:
  - type: text
outputs:
  - type: text
runtime:
  type: service
  endpoint: http://localhost:8000
tags:
  - test
"""
    manifest_path.write_text(manifest_content)
    return manifest_path


def test_loader_initialization(temp_skills_dir: Path) -> None:
    """Test ManifestLoader initialization."""
    loader = ManifestLoader(temp_skills_dir)
    assert loader.skills_dir == temp_skills_dir


def test_loader_invalid_directory() -> None:
    """Test ManifestLoader with non-existent directory."""
    with pytest.raises(ValueError, match="does not exist"):
        ManifestLoader("/nonexistent/directory")


def test_load_manifest(sample_manifest: Path, temp_skills_dir: Path) -> None:
    """Test loading a single manifest."""
    loader = ManifestLoader(temp_skills_dir)
    manifest = loader.load_manifest(sample_manifest)

    assert isinstance(manifest, SkillManifest)
    assert manifest.name == "test-skill"
    assert manifest.description == "A test skill"
    assert manifest.runtime.type == RuntimeType.SERVICE


def test_load_all_manifests(sample_manifest: Path, temp_skills_dir: Path) -> None:
    """Test loading all manifests from a directory."""
    loader = ManifestLoader(temp_skills_dir)
    manifests = loader.load_all()

    assert len(manifests) == 1
    assert manifests[0].name == "test-skill"


def test_load_all_empty_directory(temp_skills_dir: Path) -> None:
    """Test loading from an empty directory."""
    loader = ManifestLoader(temp_skills_dir)
    manifests = loader.load_all()

    assert manifests == []


def test_validate_manifests(temp_skills_dir: Path) -> None:
    """Test manifest validation."""
    # Create manifests with issues
    manifest1_path = temp_skills_dir / "skill1.yaml"
    manifest1_path.write_text(
        """
name: skill1
description: First skill
runtime:
  type: docker
tags: []
"""
    )

    manifest2_path = temp_skills_dir / "skill2.yaml"
    manifest2_path.write_text(
        """
name: skill2
description: Second skill
runtime:
  type: anthropic
tags: []
"""
    )

    loader = ManifestLoader(temp_skills_dir)
    manifests = loader.load_all()

    warnings = loader.validate_manifests(manifests)

    # Should have warnings for missing required fields
    assert "skill1" in warnings
    assert "skill2" in warnings
    assert any("image" in w for w in warnings["skill1"])
    assert any("skill_id" in w for w in warnings["skill2"])


def test_load_invalid_yaml(temp_skills_dir: Path) -> None:
    """Test loading invalid YAML."""
    invalid_path = temp_skills_dir / "invalid.yaml"
    invalid_path.write_text("{ invalid: yaml: structure: }")

    loader = ManifestLoader(temp_skills_dir)

    with pytest.raises(ValueError, match="Invalid YAML"):
        loader.load_manifest(invalid_path)


def test_load_empty_file(temp_skills_dir: Path) -> None:
    """Test loading empty file."""
    empty_path = temp_skills_dir / "empty.yaml"
    empty_path.write_text("")

    loader = ManifestLoader(temp_skills_dir)

    with pytest.raises(ValueError, match="Empty manifest"):
        loader.load_manifest(empty_path)
