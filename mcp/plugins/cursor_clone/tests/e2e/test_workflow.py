"""E2E tests for Cursor-AI Clone workflow."""
import pytest
import tempfile
from pathlib import Path
import asyncio

from mcp.plugins.cursor_clone.config import load_config
from mcp.plugins.cursor_clone.llm.engine import LLMEngineFactory
from mcp.plugins.cursor_clone.agent.repo_indexer import RepositoryIndexer
from mcp.plugins.cursor_clone.agent.planner import TaskPlanner
from mcp.plugins.cursor_clone.agent.editor import CodeEditor
from mcp.plugins.cursor_clone.agent.chat import ChatAssistant


@pytest.fixture
def temp_workspace():
    """Create temporary workspace."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        
        # Create sample files
        (workspace / "src").mkdir()
        (workspace / "src" / "main.py").write_text("""def hello():
    print("Hello")

if __name__ == "__main__":
    hello()
""")
        
        (workspace / "tests").mkdir()
        (workspace / "tests" / "__init__.py").write_text("")
        
        yield workspace


@pytest.fixture
def config():
    """Create test config."""
    return {
        "llm": {
            "model_path": "models/gemma3-4b.gguf",
            "use_gpu": False,
            "max_tokens": 1024
        },
        "indexing": {
            "enabled": True,
            "ignore_patterns": ["**/__pycache__/**"],
            "chunk_size": 100,
            "chunk_overlap": 20
        },
        "workspace": {
            "audit_log": "logs/audit.jsonl"
        }
    }


@pytest.mark.asyncio
async def test_plan_and_patch_workflow(temp_workspace, config):
    """Test plan and patch workflow."""
    # Initialize components
    llm = LLMEngineFactory.create(config.get("llm", {}))
    await llm.load()
    
    indexer = RepositoryIndexer(temp_workspace, config)
    planner = TaskPlanner(llm, config)
    editor = CodeEditor(temp_workspace, config)
    
    # Index repository
    indexer.index_repository(full=True)
    
    # Create plan
    plan_result = await planner.plan(
        goal="Add unit tests for hello function",
        scope="tests/",
        files=["src/main.py"]
    )
    
    assert "plan" in plan_result
    assert "risks" in plan_result
    assert plan_result["steps"] > 0
    
    # Generate and apply patch (mock)
    test_file = "tests/test_main.py"
    test_content = """import unittest
from src.main import hello

class TestHello(unittest.TestCase):
    def test_hello(self):
        hello()  # Should not raise

if __name__ == "__main__":
    unittest.main()
"""
    
    result = editor.apply_patch(test_file, test_content, dry_run=True)
    assert result["status"] == "would_create"
    
    result = editor.apply_patch(test_file, test_content, dry_run=False)
    assert result["status"] == "created"
    assert (temp_workspace / test_file).exists()


@pytest.mark.asyncio
async def test_chat_workflow(temp_workspace, config):
    """Test chat workflow."""
    # Initialize components
    llm = LLMEngineFactory.create(config.get("llm", {}))
    await llm.load()
    
    indexer = RepositoryIndexer(temp_workspace, config)
    chat = ChatAssistant(llm, indexer, config)
    
    # Index repository
    indexer.index_repository(full=True)
    
    # Chat
    result = await chat.chat(
        "Explain the hello function",
        context_files=["src/main.py"]
    )
    
    assert "response" in result
    assert len(result["response"]) > 0


@pytest.mark.asyncio
async def test_search_workflow(temp_workspace, config):
    """Test search workflow."""
    indexer = RepositoryIndexer(temp_workspace, config)
    indexer.index_repository(full=True)
    
    # Search
    results = indexer.search_code("hello", max_results=5)
    
    assert len(results) > 0
    assert any("hello" in r["content"].lower() for r in results)

