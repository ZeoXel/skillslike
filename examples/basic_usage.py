"""Basic usage example for SkillsLike."""

import logging

from skillslike.agent.core import create_agent, invoke_agent
from skillslike.registry import SkillRegistry
from skillslike.router import IntentRouter

# Configure logging
logging.basicConfig(level=logging.INFO)


def main() -> None:
    """Run a basic example of the SkillsLike agent."""
    print("=== SkillsLike Basic Usage Example ===\n")

    # 1. Load skills from manifests
    print("Loading skills...")
    registry = SkillRegistry("skills/")
    print(f"Loaded {len(registry.manifests)} skills\n")

    # 2. List loaded skills
    print("Available skills:")
    for manifest in registry.get_all_manifests():
        print(f"  - {manifest.name}: {manifest.description}")
    print()

    # 3. Create router
    router = IntentRouter(registry.get_all_manifests(), max_tools=3)

    # 4. Example user messages
    messages = [
        "Analyze this Excel spreadsheet",
        "Search the web for information about LangChain",
        "Summarize this document",
    ]

    for message in messages:
        print(f"User: {message}")

        # Route to relevant tools
        all_tools = registry.get_all_tools()
        selected_tools = router.route_tools(message, all_tools)

        print(f"Selected {len(selected_tools)} tools:")
        for tool in selected_tools:
            print(f"  - {tool.name}")

        # Create and invoke agent
        agent = create_agent(selected_tools)
        result = invoke_agent(agent, message, thread_id="demo-session")

        print(f"Agent: {result['text'][:200]}...")
        if result["file_ids"]:
            print(f"Files: {result['file_ids']}")
        print()


if __name__ == "__main__":
    main()
