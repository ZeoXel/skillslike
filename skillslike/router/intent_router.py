"""Intent-based router for filtering tools based on user messages."""

import logging
import re
from collections.abc import Callable

from langchain_core.tools import StructuredTool

from skillslike.models.manifest import SkillManifest

logger = logging.getLogger(__name__)


class IntentRouter:
    """Routes user messages to relevant tools using keyword matching.

    This provides progressive loading by only binding tools that match
    the user's intent, reducing context size and improving routing.
    """

    def __init__(
        self,
        manifests: list[SkillManifest],
        *,
        match_threshold: float = 0.0,
        max_tools: int = 5,
    ) -> None:
        """Initialize the intent router.

        Args:
            manifests: List of skill manifests to route against.
            match_threshold: Minimum score (0-1) for a tool to be included.
            max_tools: Maximum number of tools to return.
        """
        self.manifests = manifests
        self.match_threshold = match_threshold
        self.max_tools = max_tools

        # Build keyword index from manifests
        self._build_keyword_index()

    def _build_keyword_index(self) -> None:
        """Build keyword index from manifest descriptions and tags."""
        self.keyword_index: dict[str, list[str]] = {}

        for manifest in self.manifests:
            keywords = set()

            # Extract keywords from description
            desc_keywords = self._extract_keywords(manifest.description)
            keywords.update(desc_keywords)

            # Add tags as keywords
            keywords.update(tag.lower() for tag in manifest.tags)

            # Store keywords for this skill
            self.keyword_index[manifest.name] = list(keywords)

        logger.debug("Built keyword index for %d skills", len(self.keyword_index))

    def _extract_keywords(self, text: str) -> set[str]:
        """Extract keywords from text.

        Args:
            text: Text to extract keywords from.

        Returns:
            Set of keywords.
        """
        # Simple keyword extraction: split on whitespace and punctuation
        # Remove common Chinese and English stop words
        stop_words = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "这个",
            "那个",
            "的",
            "了",
            "在",
            "是",
            "和",
        }

        # Split English words and keep individual Chinese characters as keywords
        # This is a simple approach; for production, use jieba or similar
        words = []

        # Extract English words
        english_words = re.findall(r"[a-zA-Z]+", text.lower())
        words.extend(english_words)

        # Extract Chinese characters (each character as a keyword)
        chinese_chars = re.findall(r"[\u4e00-\u9fff]", text)
        words.extend(chinese_chars)

        # Filter stop words and short English words
        keywords = {w for w in words if (len(w) > 1 or ord(w[0]) > 127) and w not in stop_words}

        return keywords

    def _score_skill(self, skill_name: str, user_keywords: set[str]) -> float:
        """Score a skill's relevance to user keywords.

        Args:
            skill_name: Name of the skill to score.
            user_keywords: Keywords extracted from user message.

        Returns:
            Relevance score (0-1).
        """
        skill_keywords = set(self.keyword_index.get(skill_name, []))

        if not skill_keywords or not user_keywords:
            return 0.0

        # Calculate Jaccard similarity
        intersection = skill_keywords & user_keywords
        union = skill_keywords | user_keywords

        return len(intersection) / len(union) if union else 0.0

    def route_tools(
        self,
        user_message: str,
        tools: list[StructuredTool],
        *,
        get_manifest: Callable[[str], SkillManifest | None] | None = None,
    ) -> list[StructuredTool]:
        """Route user message to relevant tools.

        Args:
            user_message: The user's message.
            tools: List of all available tools.
            get_manifest: Optional function to get manifest by tool name.

        Returns:
            List of relevant tools.
        """
        if not tools:
            return []

        # Extract keywords from user message
        user_keywords = self._extract_keywords(user_message)

        if not user_keywords:
            # If no keywords, return all tools (up to max_tools)
            logger.debug("No keywords found, returning first %d tools", self.max_tools)
            return tools[: self.max_tools]

        # Score each tool
        scored_tools: list[tuple[StructuredTool, float]] = []

        for tool in tools:
            # Get skill name from tool name (convert back from snake_case)
            skill_name = tool.name.replace("_", "-")

            # Try to get manifest if function provided
            if get_manifest:
                manifest = get_manifest(skill_name)
                if manifest:
                    skill_name = manifest.name

            score = self._score_skill(skill_name, user_keywords)

            if score >= self.match_threshold:
                scored_tools.append((tool, score))

        # Sort by score (descending)
        scored_tools.sort(key=lambda x: x[1], reverse=True)

        # Return top tools
        selected_tools = [tool for tool, _ in scored_tools[: self.max_tools]]

        logger.info(
            "Routed to %d tools from %d candidates for message: %s",
            len(selected_tools),
            len(tools),
            user_message[:50],
        )

        # If no tools matched, return top tools anyway
        if not selected_tools and tools:
            logger.warning("No tools matched keywords, returning top %d tools", self.max_tools)
            selected_tools = tools[: self.max_tools]

        return selected_tools

    def get_skill_keywords(self, skill_name: str) -> list[str]:
        """Get keywords for a specific skill.

        Args:
            skill_name: Name of the skill.

        Returns:
            List of keywords for the skill.
        """
        return self.keyword_index.get(skill_name, [])
