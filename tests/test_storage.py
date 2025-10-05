"""Tests for storage module."""
import pytest
import tempfile
from pathlib import Path
from brain.model import BrainstormSession
from brain.organizer import Organizer
from storage.files import FileStorage
from storage.exporters import MarkdownExporter, CSVExporter


def test_file_storage_save_load():
    """Test saving and loading sessions."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = FileStorage(Path(tmpdir))
        
        # Create session
        session = BrainstormSession(project_name="test")
        organizer = Organizer(session)
        organizer.add_idea("Test idea")
        
        # Save
        success = storage.save_session(session)
        assert success
        assert storage.exists()
        
        # Load
        loaded = storage.load_session()
        assert loaded is not None
        assert loaded.project_name == "test"
        assert len(loaded.ideas) == 1


def test_file_storage_snapshot():
    """Test creating snapshots."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = FileStorage(Path(tmpdir))
        
        session = BrainstormSession(project_name="test")
        organizer = Organizer(session)
        organizer.add_idea("Test idea")
        
        # Create snapshot
        success = storage.create_snapshot(session)
        assert success
        
        # List snapshots
        snapshots = storage.list_snapshots()
        assert len(snapshots) == 1


def test_markdown_export():
    """Test Markdown export."""
    with tempfile.TemporaryDirectory() as tmpdir:
        session = BrainstormSession(project_name="test")
        organizer = Organizer(session)
        
        # Add content
        idea = organizer.add_idea("Test idea", tags=["test"])
        organizer.promote_idea(idea.id)
        organizer.add_action("Test action")
        organizer.add_cluster("Test Cluster", idea_ids=[idea.id])
        
        # Export
        filepath = Path(tmpdir) / "test.md"
        success = MarkdownExporter.export(session, filepath)
        assert success
        assert filepath.exists()
        
        # Check content
        content = filepath.read_text()
        assert "test" in content.lower()
        assert "Test idea" in content
        assert "Test action" in content


def test_csv_export():
    """Test CSV export."""
    with tempfile.TemporaryDirectory() as tmpdir:
        session = BrainstormSession(project_name="test")
        organizer = Organizer(session)
        
        organizer.add_idea("Idea 1", tags=["tag1"])
        organizer.add_idea("Idea 2", tags=["tag2"])
        
        # Export
        filepath = Path(tmpdir) / "test.csv"
        success = CSVExporter.export(session, filepath)
        assert success
        assert filepath.exists()
        
        # Check content
        content = filepath.read_text()
        assert "Idea 1" in content
        assert "Idea 2" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
