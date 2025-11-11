"""Unit tests for task planner."""
import pytest
from unittest.mock import Mock, AsyncMock

from mcp.plugins.cursor_clone.agent.planner import TaskPlanner


@pytest.fixture
def mock_llm():
    """Create mock LLM."""
    llm = Mock()
    llm.generate = AsyncMock(return_value="""## Plan
1. Analyze code structure
2. Implement changes
3. Test changes

## Risks
- May break existing functionality""")
    return llm


@pytest.fixture
def config():
    """Create test config."""
    return {
        "llm": {
            "max_tokens": 1024
        }
    }


@pytest.fixture
def planner(mock_llm, config):
    """Create task planner."""
    return TaskPlanner(mock_llm, config)


@pytest.mark.asyncio
async def test_plan_basic(planner):
    """Test basic planning."""
    result = await planner.plan("Add logging")
    
    assert "plan" in result
    assert "risks" in result
    assert "steps" in result
    assert result["steps"] > 0


@pytest.mark.asyncio
async def test_plan_with_scope(planner):
    """Test planning with scope."""
    result = await planner.plan("Add logging", scope="src/logging/")
    
    assert "plan" in result
    assert result["steps"] > 0


@pytest.mark.asyncio
async def test_plan_with_files(planner):
    """Test planning with files."""
    result = await planner.plan("Add logging", files=["src/main.py"])
    
    assert "plan" in result
    assert result["steps"] > 0

