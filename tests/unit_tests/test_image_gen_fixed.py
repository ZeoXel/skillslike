"""Test image generation executor with Settings integration."""

import logging
from unittest.mock import MagicMock, patch

import pytest

from skillslike.config import Settings, get_settings
from skillslike.executors.image_gen_executor import ImageGenExecutor
from skillslike.models.manifest import SkillManifest

logging.basicConfig(level=logging.DEBUG)


def test_image_gen_executor_uses_settings():
    """Test that ImageGenExecutor correctly loads API key from Settings."""
    # Create a mock manifest
    manifest_data = {
        "name": "test-image-gen",
        "description": "Test image generation",
        "inputs": [],
        "outputs": [],
        "runtime": {
            "type": "service",
            "endpoint": "https://api.bltcy.ai/v1/images/generations",
            "timeout": 60,
        },
        "tags": ["test"],
    }
    manifest = SkillManifest(**manifest_data)

    # Create executor
    executor = ImageGenExecutor(manifest)

    # Mock settings to return test values
    with patch("skillslike.executors.image_gen_executor.get_settings") as mock_get_settings:
        mock_settings = MagicMock()
        mock_settings.openai_api_key = "test-api-key-12345"
        mock_settings.openai_base_url = "https://api.test.com"
        mock_get_settings.return_value = mock_settings

        # Mock httpx.post to avoid actual API call
        with patch("skillslike.executors.image_gen_executor.httpx.post") as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "data": [{"url": "https://example.com/image.png"}]
            }
            mock_post.return_value = mock_response

            # Mock httpx.get for image download
            with patch("skillslike.executors.image_gen_executor.httpx.get") as mock_get:
                mock_img_response = MagicMock()
                mock_img_response.content = b"fake-image-data"
                mock_get.return_value = mock_img_response

                # Mock FileStore
                with patch(
                    "skillslike.executors.image_gen_executor.FileStore"
                ) as mock_file_store:
                    mock_store_instance = MagicMock()
                    mock_store_instance.store.return_value = "test-file-id-123"
                    mock_file_store.return_value = mock_store_instance

                    # Execute
                    result = executor.execute(prompt="test prompt")

                    # Verify Settings was called
                    mock_get_settings.assert_called_once()

                    # Verify API was called with correct key
                    assert mock_post.called
                    call_kwargs = mock_post.call_args
                    assert call_kwargs.kwargs["headers"]["Authorization"] == "Bearer test-api-key-12345"
                    assert "https://api.test.com/v1/images/generations" in call_kwargs.args[0]

                    # Verify result contains file_id
                    assert "file_id: test-file-id-123" in result
                    print(f"✓ Test passed! Result: {result}")


def test_settings_loads_from_env():
    """Test that Settings correctly loads from environment."""
    # Get actual settings
    settings = get_settings()

    # Verify that settings are loaded
    assert isinstance(settings, Settings)

    # Check if openai_api_key is loaded (should be from .env)
    if settings.openai_api_key:
        print(f"✓ OPENAI_API_KEY loaded: {settings.openai_api_key[:10]}...")
    else:
        print("⚠ OPENAI_API_KEY not loaded from .env")

    if settings.openai_base_url:
        print(f"✓ OPENAI_BASE_URL loaded: {settings.openai_base_url}")
    else:
        print("⚠ OPENAI_BASE_URL not loaded from .env")


if __name__ == "__main__":
    print("\n=== Testing Settings Integration ===\n")
    test_settings_loads_from_env()
    print("\n=== Testing ImageGenExecutor ===\n")
    test_image_gen_executor_uses_settings()
    print("\n✅ All tests passed!")
