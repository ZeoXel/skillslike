"""Pydantic schemas for tool arguments."""

from pydantic import BaseModel, Field


class ImageGenInput(BaseModel):
    """Input schema for image generation tool."""

    prompt: str = Field(description="Description of the image to generate")
    aspect_ratio: str = Field(
        default="1:1",
        description="Aspect ratio of the image (1:1, 4:3, 16:9, etc.)",
    )
    image_size: str = Field(
        default="4K",
        description="Image resolution: 1K, 2K, or 4K",
    )
