"""Registry for managing skills and converting them to LangChain tools."""

import logging
from pathlib import Path

from langchain_core.tools import StructuredTool

from skillslike.models.manifest import SkillManifest
from skillslike.registry.loader import ManifestLoader

logger = logging.getLogger(__name__)


class SkillRegistry:
    """Registry for managing skills and their corresponding tools."""

    def __init__(self, skills_dir: str | Path) -> None:
        """Initialize the skill registry.

        Args:
            skills_dir: Directory containing skill manifest files.
        """
        self.loader = ManifestLoader(skills_dir)
        self.manifests: dict[str, SkillManifest] = {}
        self.tools: dict[str, StructuredTool] = {}
        self._load_manifests()

    def _load_manifests(self) -> None:
        """Load all skill manifests from the skills directory."""
        manifests = self.loader.load_all()

        # Validate manifests
        warnings = self.loader.validate_manifests(manifests)
        for skill_name, skill_warnings in warnings.items():
            for warning in skill_warnings:
                logger.warning("Skill '%s': %s", skill_name, warning)

        # Store manifests by name
        self.manifests = {m.name: m for m in manifests}
        logger.info("Loaded %d skill manifests", len(self.manifests))

    def get_manifest(self, name: str) -> SkillManifest | None:
        """Get a skill manifest by name.

        Args:
            name: The skill name.

        Returns:
            The skill manifest, or `None` if not found.
        """
        return self.manifests.get(name)

    def get_all_manifests(self) -> list[SkillManifest]:
        """Get all loaded skill manifests.

        Returns:
            List of all skill manifests.
        """
        return list(self.manifests.values())

    def build_tool(self, manifest: SkillManifest) -> StructuredTool:
        """Build a LangChain StructuredTool from a skill manifest.

        Args:
            manifest: The skill manifest to convert.

        Returns:
            A StructuredTool instance for the skill.

        Note:
            The actual tool function will be wired to executors.
            This is a placeholder that returns metadata.
        """
        # Import here to avoid circular dependency
        from skillslike.executors.anthropic_executor import AnthropicExecutor
        from skillslike.executors.custom_executor import CustomExecutor
        from skillslike.executors.image_gen_executor import ImageGenExecutor

        # Choose executor based on runtime type or skill name
        if manifest.name == "nano-banana-image-gen":
            executor = ImageGenExecutor(manifest)
            # Use Pydantic schema for image generation
            tool = StructuredTool.from_function(
                func=executor.execute,
                name=manifest.name.replace("-", "_"),
                description=manifest.description,
                args_schema=executor.get_input_schema(),
            )
        elif manifest.runtime.type == "anthropic":
            executor = AnthropicExecutor(manifest)
            tool = StructuredTool.from_function(
                func=executor.execute,
                name=manifest.name.replace("-", "_"),
                description=manifest.description,
            )
        else:
            executor = CustomExecutor(manifest)
            tool = StructuredTool.from_function(
                func=executor.execute,
                name=manifest.name.replace("-", "_"),
                description=manifest.description,
            )

        return tool

    def get_tool(self, name: str) -> StructuredTool | None:
        """Get a tool by skill name.

        Args:
            name: The skill name.

        Returns:
            The tool instance, or `None` if not found.
        """
        if name in self.tools:
            return self.tools[name]

        manifest = self.get_manifest(name)
        if not manifest:
            return None

        tool = self.build_tool(manifest)
        self.tools[name] = tool
        return tool

    def get_all_tools(self) -> list[StructuredTool]:
        """Get all tools for all loaded skills.

        Returns:
            List of all tools.
        """
        tools = []
        for name in self.manifests:
            tool = self.get_tool(name)
            if tool:
                tools.append(tool)
        return tools

    def reload(self) -> None:
        """Reload all manifests from disk."""
        self.manifests.clear()
        self.tools.clear()
        self._load_manifests()
        logger.info("Registry reloaded")
