"""Unit tests for repository indexer."""
import pytest
import tempfile
from pathlib import Path

from mcp.plugins.cursor_clone.agent.repo_indexer import RepositoryIndexer


@pytest.fixture
def temp_dir():
    """Create temporary directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def config():
    """Create test config."""
    return {
        "indexing": {
            "ignore_patterns": ["**/__pycache__/**"],
            "chunk_size": 100,
            "chunk_overlap": 20
        }
    }


@pytest.fixture
def indexer(temp_dir, config):
    """Create repository indexer."""
    return RepositoryIndexer(temp_dir, config)


def test_should_ignore(indexer, temp_dir):
    """Test ignore pattern matching."""
    # Create ignored file
    ignored = temp_dir / "__pycache__" / "test.pyc"
    ignored.parent.mkdir()
    ignored.write_bytes(b"test")
    
    assert indexer.should_ignore(ignored)
    
    # Create non-ignored file
    normal = temp_dir / "test.py"
    normal.write_text("def hello(): pass")
    
    assert not indexer.should_ignore(normal)


def test_index_repository(indexer, temp_dir):
    """Test repository indexing."""
    # Create test files
    (temp_dir / "test1.py").write_text("def hello():\n    print('Hello')\n")
    (temp_dir / "test2.py").write_text("class Test:\n    pass\n")
    
    stats = indexer.index_repository(full=True)
    
    assert stats["files_indexed"] == 2
    assert stats["chunks_indexed"] > 0
    assert len(indexer.index) > 0


def test_search_code(indexer, temp_dir):
    """Test code search."""
    # Create and index file
    (temp_dir / "test.py").write_text("def hello():\n    print('Hello')\n")
    indexer.index_repository(full=True)
    
    # Search
    results = indexer.search_code("hello", max_results=10)
    
    assert len(results) > 0
    assert any("hello" in r["content"].lower() for r in results)


def test_find_symbol(indexer, temp_dir):
    """Test symbol finding."""
    # Create and index file
    (temp_dir / "test.py").write_text("def hello():\n    pass\nclass Test:\n    pass\n")
    indexer.index_repository(full=True)
    
    # Find symbol
    results = indexer.find_symbol("hello")
    
    assert len(results) > 0
    assert any(s["name"] == "hello" for s in results)

