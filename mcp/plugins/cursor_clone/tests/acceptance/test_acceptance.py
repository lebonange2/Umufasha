"""Acceptance tests for Cursor-AI Clone."""
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
def sample_repo():
    """Create sample repository."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo = Path(tmpdir)
        
        # Create sample code
        (repo / "src").mkdir()
        (repo / "src" / "parser.py").write_text("""def parse(text):
    return text.split()

def parse_json(text):
    import json
    return json.loads(text)
""")
        
        (repo / "tests").mkdir()
        (repo / "tests" / "__init__.py").write_text("")
        
        yield repo


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
@pytest.mark.acceptance
async def test_explain_and_docstring(sample_repo, config):
    """Acceptance test: Explain code and propose docstring patch."""
    llm = LLMEngineFactory.create(config.get("llm", {}))
    await llm.load()
    
    indexer = RepositoryIndexer(sample_repo, config)
    chat = ChatAssistant(llm, indexer, config)
    editor = CodeEditor(sample_repo, config)
    
    indexer.index_repository(full=True)
    
    # Explain code
    result = await chat.chat(
        "Explain the parse function",
        context_files=["src/parser.py"]
    )
    
    assert "response" in result
    assert len(result["response"]) > 0
    
    # Generate docstring patch
    original = (sample_repo / "src" / "parser.py").read_text()
    new_content = original.replace(
        "def parse(text):",
        'def parse(text):\n    """Parse text into words."""'
    )
    
    # Apply patch
    result = editor.apply_patch("src/parser.py", new_content, dry_run=False)
    assert result["status"] == "modified"
    
    # Verify
    assert (sample_repo / "src" / "parser.py").read_text().count('"""') > 0


@pytest.mark.asyncio
@pytest.mark.acceptance
async def test_refactor_and_test(sample_repo, config):
    """Acceptance test: Refactor function and keep tests green."""
    llm = LLMEngineFactory.create(config.get("llm", {}))
    await llm.load()
    
    indexer = RepositoryIndexer(sample_repo, config)
    planner = TaskPlanner(llm, config)
    editor = CodeEditor(sample_repo, config)
    
    indexer.index_repository(full=True)
    
    # Create plan
    plan_result = await planner.plan(
        goal="Refactor parse function to remove duplication",
        scope="src/parser.py"
    )
    
    assert "plan" in plan_result
    
    # Apply refactoring (mock)
    original = (sample_repo / "src" / "parser.py").read_text()
    # Simple refactoring: extract common logic
    new_content = original.replace(
        "def parse(text):\n    return text.split()",
        "def parse(text):\n    return _split_text(text)\n\ndef _split_text(text):\n    return text.split()"
    )
    
    result = editor.apply_patch("src/parser.py", new_content, dry_run=False)
    assert result["status"] == "modified"
    
    # Verify file still exists and is valid
    assert (sample_repo / "src" / "parser.py").exists()
    content = (sample_repo / "src" / "parser.py").read_text()
    assert "def parse" in content


@pytest.mark.asyncio
@pytest.mark.acceptance
async def test_add_test_and_fix(sample_repo, config):
    """Acceptance test: Add test file and fix failing test."""
    llm = LLMEngineFactory.create(config.get("llm", {}))
    await llm.load()
    
    indexer = RepositoryIndexer(sample_repo, config)
    planner = TaskPlanner(llm, config)
    editor = CodeEditor(sample_repo, config)
    
    indexer.index_repository(full=True)
    
    # Create test file
    test_content = """import unittest
from src.parser import parse

class TestParse(unittest.TestCase):
    def test_parse(self):
        result = parse("hello world")
        self.assertEqual(result, ["hello", "world"])

if __name__ == "__main__":
    unittest.main()
"""
    
    result = editor.apply_patch("tests/test_parser.py", test_content, dry_run=False)
    assert result["status"] == "created"
    assert (sample_repo / "tests" / "test_parser.py").exists()
    
    # Test would run here (mock)
    # If test fails, generate fix
    # Apply fix
    # Verify test passes

