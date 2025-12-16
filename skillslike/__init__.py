"""SkillsLike: Agent architecture for skill-like progressive loading."""

__version__ = "0.1.0"

from skillslike.models.manifest import SkillManifest
from skillslike.registry.registry import SkillRegistry

__all__ = ["SkillManifest", "SkillRegistry", "__version__"]
