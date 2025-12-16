"""Executor for image generation using nano-banana-2 API."""

import base64
import json
import logging

import httpx
from pydantic import BaseModel, Field

from skillslike.executors.base import BaseExecutor

logger = logging.getLogger(__name__)


class ImageGenInput(BaseModel):
    """Input schema for image generation."""

    prompt: str = Field(description="Description of the image to generate in Chinese or English")
    aspect_ratio: str = Field(
        default="1:1",
        description="Image aspect ratio: 1:1, 4:3, 16:9, 9:16, etc.",
    )
    image_size: str = Field(
        default="4K",
        description="Image resolution: 1K, 2K, or 4K (high quality)",
    )


class ImageGenExecutor(BaseExecutor):
    """Executor for nano-banana-2 image generation.

    Calls the DALL-E compatible API to generate images from text prompts.
    """

    def get_input_schema(self) -> type[BaseModel]:
        """Get the input schema for this executor.

        Returns:
            Pydantic model class for input validation.
        """
        return ImageGenInput

    def execute(self, prompt: str, aspect_ratio: str = "1:1", image_size: str = "4K") -> str:
        """Execute image generation.

        Args:
            prompt: Description of the image to generate.
            aspect_ratio: Image aspect ratio (default "1:1").
            image_size: Image resolution 1K/2K/4K (default "4K").

        Returns:
            Execution result with image URL and file_id.

        Raises:
            RuntimeError: If API call fails.
        """
        if not prompt:
            msg = "Image generation requires a 'prompt' parameter"
            raise RuntimeError(msg)

        response_format = "url"

        logger.info(
            "Generating image with nano-banana-2: prompt='%s', ratio=%s, size=%s",
            prompt[:50],
            aspect_ratio,
            image_size,
        )

        # Get API credentials from Settings
        from skillslike.config import get_settings

        settings = get_settings()
        api_key = settings.openai_api_key
        base_url = settings.openai_base_url or "https://api.bltcy.ai"

        if not api_key:
            msg = "API key not found. Set OPENAI_API_KEY in .env file."
            raise RuntimeError(msg)

        # Ensure base_url doesn't end with /v1
        if base_url.endswith("/v1"):
            base_url = base_url[:-3]

        # Prepare request
        endpoint = f"{base_url}/v1/images/generations"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": "nano-banana-2",
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
            "image_size": image_size,
            "response_format": response_format,
        }

        try:
            logger.debug("Calling image generation API: %s", endpoint)
            logger.debug("Payload: %s", json.dumps(payload))

            response = httpx.post(
                endpoint,
                headers=headers,
                json=payload,
                timeout=self.manifest.runtime.timeout,
            )
            response.raise_for_status()

            result = response.json()
            logger.debug("Image generation response: %s", json.dumps(result)[:200])

            # Parse response
            if "data" in result and len(result["data"]) > 0:
                image_data = result["data"][0]

                if response_format == "url" and "url" in image_data:
                    # URL format
                    image_url = image_data["url"]
                    logger.info("Generated image URL: %s", image_url)

                    # Download and store the image
                    file_id = self._download_and_store_image(image_url)

                    return f"图片生成成功！\n\n描述: {prompt}\n比例: {aspect_ratio}\n分辨率: {image_size}\n\nfile_id: {file_id}\n图片URL: {image_url}"

                elif response_format == "b64_json" and "b64_json" in image_data:
                    # Base64 format
                    b64_data = image_data["b64_json"]
                    file_id = self._store_base64_image(b64_data)

                    return f"图片生成成功！\n\n描述: {prompt}\n比例: {aspect_ratio}\n分辨率: {image_size}\n\nfile_id: {file_id}"

                else:
                    msg = f"Unexpected response format: {result}"
                    raise RuntimeError(msg)

            else:
                msg = f"No image data in response: {result}"
                raise RuntimeError(msg)

        except httpx.HTTPError as e:
            msg = f"Image generation API call failed: {e}"
            logger.error(msg)
            if hasattr(e, "response") and e.response is not None:
                logger.error("Response body: %s", e.response.text)
            raise RuntimeError(msg) from e

    def _download_and_store_image(self, image_url: str) -> str:
        """Download image from URL and store it.

        Args:
            image_url: URL of the generated image.

        Returns:
            File ID of the stored image.
        """
        try:
            # Download image
            logger.debug("Downloading image from: %s", image_url)
            response = httpx.get(image_url, timeout=30)
            response.raise_for_status()

            # Store in file store
            from skillslike.storage import FileStore

            file_store = FileStore()
            file_id = file_store.store(
                response.content,
                filename="generated_image.png",
                content_type="image/png",
            )

            logger.info("Stored image with file_id: %s", file_id)
            return file_id

        except Exception as e:
            logger.error("Failed to download/store image: %s", e)
            # Return a placeholder if download fails
            return "download-failed"

    def _store_base64_image(self, b64_data: str) -> str:
        """Store base64 encoded image.

        Args:
            b64_data: Base64 encoded image data.

        Returns:
            File ID of the stored image.
        """
        try:
            # Decode base64
            image_bytes = base64.b64decode(b64_data)

            # Store in file store
            from skillslike.storage import FileStore

            file_store = FileStore()
            file_id = file_store.store(
                image_bytes,
                filename="generated_image.png",
                content_type="image/png",
            )

            logger.info("Stored base64 image with file_id: %s", file_id)
            return file_id

        except Exception as e:
            logger.error("Failed to store base64 image: %s", e)
            return "storage-failed"
