"""Direct API test for nano-banana-2."""

import httpx

# API configuration
API_KEY = "sk-JO438PQ5WpZFtR9Gt5tMN119FmD1bG6YDtmczNgGyDIMCHc1"
BASE_URL = "https://api.bltcy.ai/v1"

print("🧪 Testing nano-banana-2 API directly...\n")

# Test payload
payload = {
    "model": "nano-banana-2",
    "prompt": "a cute cat",
    "aspect_ratio": "1:1",
    "image_size": "4K",
    "response_format": "url",
}

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}

endpoint = f"{BASE_URL}/images/generations"

print(f"📍 Endpoint: {endpoint}")
print(f"📦 Payload: {payload}\n")

try:
    print("⏳ Sending request...")
    response = httpx.post(
        endpoint,
        headers=headers,
        json=payload,
        timeout=90.0,
    )

    print(f"✅ Status code: {response.status_code}")
    print("📄 Response headers:")
    for key, value in response.headers.items():
        if key.lower() in ["content-type", "content-length"]:
            print(f"   {key}: {value}")

    print("\n📝 Response content (first 500 chars):")
    print(response.text[:500])

    if response.status_code == 200:
        try:
            data = response.json()
            print("\n✨ Success! Parsed JSON:")
            print(f"   Keys: {list(data.keys())}")

            if "data" in data and len(data["data"]) > 0:
                img_data = data["data"][0]
                print("\n🖼️ Image info:")
                if "url" in img_data:
                    print(f"   URL: {img_data['url'][:80]}...")
                if "b64_json" in img_data:
                    print(f"   Base64: {img_data['b64_json'][:80]}...")
        except Exception as e:
            print(f"\n❌ JSON parsing failed: {e}")
    else:
        print(f"\n❌ Request failed with status {response.status_code}")

except httpx.TimeoutException:
    print("⏱️ Request timed out after 90 seconds")
except Exception as e:
    print(f"❌ Error: {type(e).__name__}: {e}")

print("\n✨ Test complete!")
