"""Test script for image generation skill."""

import requests

API_BASE = "http://localhost:8000"


def test_image_generation():
    """Test the image generation skill."""
    print("🎨 Testing Nano-Banana-2 Image Generation\n")

    # Test request
    request_data = {
        "message": "帮我画一只可爱的橘猫",
        "thread_id": "test-image-gen-001"
    }

    print(f"📤 Sending request:")
    print(f"   Message: {request_data['message']}")
    print(f"   Thread ID: {request_data['thread_id']}\n")

    try:
        response = requests.post(
            f"{API_BASE}/api/chat",
            json=request_data,
            timeout=90  # Image generation may take time
        )

        print(f"📥 Response status: {response.status_code}\n")

        if response.status_code == 200:
            result = response.json()
            print("✅ Success!")
            print(f"\n📝 Response text:")
            print(result['text'])
            print(f"\n📎 Files: {result.get('files', [])}")
            print(f"🔗 Thread ID: {result['thread_id']}")

            if result.get('files'):
                file_id = result['files'][0]
                print(f"\n🖼️  Image URL: {API_BASE}/api/file/{file_id}")
                print(f"\n💡 Open this URL in your browser to see the image!")

        else:
            print(f"❌ Failed: {response.status_code}")
            print(response.text)

    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    test_image_generation()
