"""Example API client for the SkillsLike API."""

import httpx


def main() -> None:
    """Example usage of the SkillsLike API."""
    base_url = "http://localhost:8000"

    print("=== SkillsLike API Client Example ===\n")

    # 1. Health check
    print("1. Checking API health...")
    response = httpx.get(f"{base_url}/health")
    print(f"Status: {response.json()}\n")

    # 2. List skills
    print("2. Listing available skills...")
    response = httpx.get(f"{base_url}/api/skills")
    skills = response.json()
    for skill in skills:
        print(f"  - {skill['name']}: {skill['description']}")
    print()

    # 3. Chat with agent
    print("3. Sending chat message...")
    chat_request = {
        "message": "Analyze the sales data in my Excel file",
        "thread_id": "example-session-1",
    }

    response = httpx.post(f"{base_url}/api/chat", json=chat_request)
    result = response.json()

    print(f"Response: {result['text']}")
    print(f"Thread ID: {result['thread_id']}")

    if result.get("files"):
        print(f"Files: {result['files']}")
        # Download first file
        file_id = result["files"][0]
        print(f"\n4. Downloading file {file_id}...")
        file_response = httpx.get(f"{base_url}/api/file/{file_id}")
        print(f"File size: {len(file_response.content)} bytes")


if __name__ == "__main__":
    main()
