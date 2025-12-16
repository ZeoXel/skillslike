"""Executor for custom skills via Docker/service endpoints."""

import json
import logging
from typing import Any

import httpx

from skillslike.executors.base import BaseExecutor

logger = logging.getLogger(__name__)


class CustomExecutor(BaseExecutor):
    """Executor for custom skills via Docker or service endpoints.

    Supports both Docker container execution and HTTP service calls.
    """

    def execute(self, **kwargs: Any) -> str:
        """Execute a custom skill.

        Args:
            **kwargs: Skill arguments.

        Returns:
            Execution result with text and optional file_id.

        Raises:
            TimeoutError: If execution exceeds timeout.
            RuntimeError: If execution fails.
        """
        runtime_type = self.manifest.runtime.type

        logger.info(
            "Executing custom skill '%s' (runtime: %s)",
            self.manifest.name,
            runtime_type,
        )

        try:
            if runtime_type == "service":
                return self._execute_service(kwargs)
            elif runtime_type == "docker":
                return self._execute_docker(kwargs)
            else:
                msg = f"Unsupported runtime type: {runtime_type}"
                raise RuntimeError(msg)

        except TimeoutError as e:
            msg = f"Skill '{self.manifest.name}' timed out after {self.manifest.runtime.timeout}s"
            logger.error(msg)
            raise TimeoutError(msg) from e

    def _execute_service(self, kwargs: dict[str, Any]) -> str:
        """Execute skill via HTTP service endpoint.

        Args:
            kwargs: Skill arguments.

        Returns:
            Service response text.
        """
        endpoint = self.manifest.runtime.endpoint

        if not endpoint:
            msg = f"Service runtime for '{self.manifest.name}' missing endpoint"
            raise RuntimeError(msg)

        logger.debug("Calling service endpoint: %s", endpoint)

        # Call the service endpoint
        try:
            response = httpx.post(
                endpoint,
                json=kwargs,
                timeout=self.manifest.runtime.timeout,
            )
            response.raise_for_status()

            result = response.json()

            # Extract text and file_id if present
            text = result.get("text", str(result))
            file_id = result.get("file_id")

            if file_id:
                text += f"\nfile_id: {file_id}"

            logger.info("Service call completed successfully")
            return text

        except httpx.HTTPError as e:
            msg = f"Service call failed: {e}"
            logger.error(msg)
            raise RuntimeError(msg) from e

    def _execute_docker(self, kwargs: dict[str, Any]) -> str:
        """Execute skill via Docker container.

        Args:
            kwargs: Skill arguments.

        Returns:
            Container output.
        """
        image = self.manifest.runtime.image
        cmd = self.manifest.runtime.cmd

        if not image:
            msg = f"Docker runtime for '{self.manifest.name}' missing image"
            raise RuntimeError(msg)

        logger.debug("Running Docker container: %s", image)

        # TODO: Implement actual Docker execution
        # This would:
        # 1. Create a container with the specified image
        # 2. Mount volumes if needed
        # 3. Pass environment variables
        # 4. Run the command
        # 5. Capture output
        # 6. Upload any output files to file store
        # 7. Return text + file_id

        # Placeholder implementation
        result_text = (
            f"[Docker Container Executed: {self.manifest.name}]\n"
            f"Image: {image}\n"
            f"Command: {cmd}\n"
            f"Arguments: {json.dumps(kwargs)}\n"
            "Note: This is a placeholder. Implement actual Docker execution."
        )

        logger.info("Docker execution completed")

        return result_text
