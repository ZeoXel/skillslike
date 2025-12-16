"""Base executor interface for skill execution."""

from abc import ABC, abstractmethod
from typing import Any

from skillslike.models.manifest import SkillManifest


class BaseExecutor(ABC):
    """Base class for skill executors."""

    def __init__(self, manifest: SkillManifest) -> None:
        """Initialize the executor.

        Args:
            manifest: The skill manifest.
        """
        self.manifest = manifest

    @abstractmethod
    def execute(self, **kwargs: Any) -> str:
        """Execute the skill with given arguments.

        Args:
            **kwargs: Skill-specific arguments.

        Returns:
            Execution result as a string.

        Raises:
            TimeoutError: If execution exceeds timeout.
            RuntimeError: If execution fails.
        """
        pass
