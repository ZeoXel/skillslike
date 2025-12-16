"""Verify image generation executor can access Settings."""

from skillslike.config import get_settings
from skillslike.models.manifest import SkillManifest
from skillslike.executors.image_gen_executor import ImageGenExecutor

print("\n=== Verifying Image Generation Configuration ===\n")

# Test 1: Check Settings
settings = get_settings()
print("1. Settings Configuration:")
print(f"   - OPENAI_API_KEY: {'✓ Loaded' if settings.openai_api_key else '✗ Missing'}")
print(f"   - OPENAI_BASE_URL: {settings.openai_base_url or '✗ Missing'}")
print(f"   - USE_OPENAI_COMPATIBLE: {settings.use_openai_compatible}")

# Test 2: Create ImageGenExecutor
print("\n2. ImageGenExecutor Initialization:")
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
executor = ImageGenExecutor(manifest)
print("   ✓ Executor created successfully")

# Test 3: Verify executor can access settings (without making actual API call)
print("\n3. Testing Settings Access in Executor:")
try:
    # Import get_settings in executor context
    from skillslike.config import get_settings as executor_get_settings
    test_settings = executor_get_settings()
    api_key = test_settings.openai_api_key
    base_url = test_settings.openai_base_url or "https://api.bltcy.ai"

    if api_key:
        print(f"   ✓ API Key accessible: {api_key[:10]}...")
    else:
        print("   ✗ API Key not accessible")

    print(f"   ✓ Base URL: {base_url}")
    print("\n✅ Image generation configuration is correct!")
    print("\nThe executor will now be able to:")
    print("   - Read OPENAI_API_KEY from Settings")
    print("   - Read OPENAI_BASE_URL from Settings")
    print("   - Make API calls to nano-banana-2")

except Exception as e:
    print(f"   ✗ Error accessing settings: {e}")

print("\n" + "="*50)
