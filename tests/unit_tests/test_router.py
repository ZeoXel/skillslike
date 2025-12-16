"""Unit tests for intent router."""

import pytest
from langchain_core.tools import StructuredTool

from skillslike.models.manifest import RuntimeConfig, RuntimeType, SkillManifest
from skillslike.router.intent_router import IntentRouter


@pytest.fixture
def sample_manifests() -> list[SkillManifest]:
    """Create sample manifests for testing."""
    return [
        SkillManifest(
            name="excel-skill",
            description="Analyze Excel spreadsheets and data",
            runtime=RuntimeConfig(type=RuntimeType.SERVICE, endpoint="http://test"),
            tags=["excel", "data", "spreadsheet"],
        ),
        SkillManifest(
            name="web-search",
            description="Search the web for information",
            runtime=RuntimeConfig(type=RuntimeType.SERVICE, endpoint="http://test"),
            tags=["search", "web"],
        ),
        SkillManifest(
            name="summarize-docs",
            description="Summarize and reorganize documents",
            runtime=RuntimeConfig(type=RuntimeType.SERVICE, endpoint="http://test"),
            tags=["summarization", "documents"],
        ),
    ]


@pytest.fixture
def sample_tools() -> list[StructuredTool]:
    """Create sample tools for testing."""

    def dummy_func() -> str:
        return "result"

    return [
        StructuredTool.from_function(func=dummy_func, name="excel_skill", description="Excel"),
        StructuredTool.from_function(func=dummy_func, name="web_search", description="Web"),
        StructuredTool.from_function(
            func=dummy_func, name="summarize_docs", description="Summarize"
        ),
    ]


def test_router_initialization(sample_manifests: list[SkillManifest]) -> None:
    """Test IntentRouter initialization."""
    router = IntentRouter(sample_manifests)

    assert len(router.keyword_index) == 3
    assert "excel-skill" in router.keyword_index
    assert "web-search" in router.keyword_index


def test_keyword_extraction() -> None:
    """Test keyword extraction from text."""
    router = IntentRouter([])

    keywords = router._extract_keywords("Analyze the Excel spreadsheet data")

    assert "analyze" in keywords
    assert "excel" in keywords
    assert "spreadsheet" in keywords
    assert "data" in keywords


def test_keyword_extraction_chinese() -> None:
    """Test keyword extraction with Chinese text.

    Note: Current implementation uses character-level extraction for simplicity.
    For production, consider using jieba or similar for proper word segmentation.
    """
    router = IntentRouter([])

    keywords = router._extract_keywords("分析这个表格数据")

    # Current implementation extracts individual Chinese characters
    assert "分" in keywords
    assert "析" in keywords
    assert "表" in keywords
    assert "格" in keywords
    assert "数" in keywords
    assert "据" in keywords
    # Verify keywords were extracted
    assert len(keywords) > 0


def test_route_tools_exact_match(
    sample_manifests: list[SkillManifest], sample_tools: list[StructuredTool]
) -> None:
    """Test routing with exact keyword match."""
    router = IntentRouter(sample_manifests, max_tools=5)

    selected = router.route_tools("Analyze Excel spreadsheet", sample_tools)

    # Should prefer excel-skill
    assert len(selected) > 0
    assert any(tool.name == "excel_skill" for tool in selected)


def test_route_tools_no_keywords(
    sample_manifests: list[SkillManifest], sample_tools: list[StructuredTool]
) -> None:
    """Test routing with no keywords."""
    router = IntentRouter(sample_manifests, max_tools=2)

    selected = router.route_tools("", sample_tools)

    # Should return up to max_tools
    assert len(selected) <= 2


def test_route_tools_max_limit(
    sample_manifests: list[SkillManifest], sample_tools: list[StructuredTool]
) -> None:
    """Test routing respects max_tools limit."""
    router = IntentRouter(sample_manifests, max_tools=1)

    selected = router.route_tools("Analyze Excel and search web", sample_tools)

    assert len(selected) <= 1


def test_get_skill_keywords(sample_manifests: list[SkillManifest]) -> None:
    """Test retrieving keywords for a specific skill."""
    router = IntentRouter(sample_manifests)

    keywords = router.get_skill_keywords("excel-skill")

    assert "excel" in keywords
    assert "data" in keywords
    assert "spreadsheet" in keywords
