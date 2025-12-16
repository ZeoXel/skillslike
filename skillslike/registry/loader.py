"""Manifest loader for reading skill definitions from YAML files."""

import logging
from pathlib import Path

import yaml
from pydantic import ValidationError

from skillslike.models.manifest import SkillManifest

logger = logging.getLogger(__name__)


class ManifestLoader:
    """Loads skill manifests from YAML files."""

    def __init__(self, skills_dir: str | Path) -> None:
        """Initialize the manifest loader.

        Args:
            skills_dir: Directory containing skill manifest files.
        """
        self.skills_dir = Path(skills_dir)
        if not self.skills_dir.exists():
            msg = f"Skills directory does not exist: {self.skills_dir}"
            raise ValueError(msg)

    def load_all(self) -> list[SkillManifest]:
        """Load all skill manifests from the skills directory.

        Returns:
            List of validated skill manifests.

        Raises:
            ValidationError: If any manifest fails validation.
        """
        manifests: list[SkillManifest] = []

        # Find all YAML files recursively
        yaml_files = list(self.skills_dir.rglob("*.yaml")) + list(
            self.skills_dir.rglob("*.yml")
        )

        if not yaml_files:
            logger.warning("No manifest files found in %s", self.skills_dir)
            return manifests

        for file_path in yaml_files:
            try:
                manifest = self.load_manifest(file_path)
                manifests.append(manifest)
                logger.info("Loaded skill manifest: %s", manifest.name)
            except (ValidationError, ValueError) as e:
                logger.error("Failed to load manifest from %s: %s", file_path, e)
                raise

        return manifests

    def load_manifest(self, file_path: str | Path) -> SkillManifest:
        """Load a single skill manifest from a YAML file.

        Args:
            file_path: Path to the manifest YAML file.

        Returns:
            Validated skill manifest.

        Raises:
            ValidationError: If manifest fails validation.
            ValueError: If file cannot be read or parsed.
        """
        file_path = Path(file_path)

        if not file_path.exists():
            msg = f"Manifest file does not exist: {file_path}"
            raise ValueError(msg)

        try:
            with file_path.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not data:
                msg = f"Empty manifest file: {file_path}"
                raise ValueError(msg)

            return SkillManifest.model_validate(data)

        except yaml.YAMLError as e:
            msg = f"Invalid YAML in {file_path}: {e}"
            raise ValueError(msg) from e

    def validate_manifests(self, manifests: list[SkillManifest]) -> dict[str, list[str]]:
        """Validate a list of manifests for conflicts and issues.

        Args:
            manifests: List of skill manifests to validate.

        Returns:
            Dictionary mapping skill names to list of validation warnings.
        """
        warnings: dict[str, list[str]] = {}
        names = [m.name for m in manifests]

        # Check for duplicate names
        if len(names) != len(set(names)):
            duplicates = [name for name in names if names.count(name) > 1]
            for dup in set(duplicates):
                warnings.setdefault(dup, []).append(f"Duplicate skill name: {dup}")

        # Validate runtime configurations
        for manifest in manifests:
            skill_warnings = []

            # Check required fields based on runtime type
            if manifest.runtime.type == "docker" and not manifest.runtime.image:
                skill_warnings.append("Docker runtime requires 'image' field")

            if manifest.runtime.type == "service" and not manifest.runtime.endpoint:
                skill_warnings.append("Service runtime requires 'endpoint' field")

            if manifest.runtime.type == "anthropic" and not manifest.runtime.skill_id:
                skill_warnings.append("Anthropic runtime requires 'skill_id' field")

            if skill_warnings:
                warnings[manifest.name] = skill_warnings

        return warnings
