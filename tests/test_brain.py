"""Tests for brain module."""
import pytest
from datetime import datetime
from brain.model import (
    Idea, Cluster, ActionItem, BrainstormSession,
    IdeaSource, Priority
)
from brain.organizer import Organizer


def test_idea_creation():
    """Test idea creation."""
    idea = Idea.create("Test idea", source=IdeaSource.USER, tags=["test"])
    
    assert idea.text == "Test idea"
    assert idea.source == IdeaSource.USER
    assert "test" in idea.tags
    assert idea.id is not None
    assert isinstance(idea.timestamp, datetime)


def test_idea_serialization():
    """Test idea to/from dict."""
    idea = Idea.create("Test idea", tags=["test"])
    data = idea.to_dict()
    
    assert data['text'] == "Test idea"
    assert data['tags'] == ["test"]
    
    restored = Idea.from_dict(data)
    assert restored.text == idea.text
    assert restored.id == idea.id


def test_session_creation():
    """Test session creation."""
    session = BrainstormSession(project_name="test")
    
    assert session.project_name == "test"
    assert len(session.ideas) == 0
    assert len(session.clusters) == 0
    assert len(session.actions) == 0


def test_organizer_add_idea():
    """Test adding ideas through organizer."""
    session = BrainstormSession(project_name="test")
    organizer = Organizer(session)
    
    idea = organizer.add_idea("Test idea", tags=["test"])
    
    assert len(session.ideas) == 1
    assert session.ideas[0].text == "Test idea"
    assert "test" in session.ideas[0].tags


def test_organizer_tag_idea():
    """Test tagging ideas."""
    session = BrainstormSession(project_name="test")
    organizer = Organizer(session)
    
    idea = organizer.add_idea("Test idea")
    success = organizer.tag_idea(idea.id, ["tag1", "tag2"])
    
    assert success
    assert "tag1" in idea.tags
    assert "tag2" in idea.tags


def test_organizer_promote_idea():
    """Test promoting ideas."""
    session = BrainstormSession(project_name="test")
    organizer = Organizer(session)
    
    idea = organizer.add_idea("Test idea")
    assert not idea.promoted
    
    organizer.promote_idea(idea.id)
    assert idea.promoted


def test_organizer_add_action():
    """Test adding action items."""
    session = BrainstormSession(project_name="test")
    organizer = Organizer(session)
    
    action = organizer.add_action("Do something", priority=Priority.HIGH)
    
    assert len(session.actions) == 1
    assert action.text == "Do something"
    assert action.priority == Priority.HIGH
    assert not action.completed


def test_organizer_complete_action():
    """Test completing actions."""
    session = BrainstormSession(project_name="test")
    organizer = Organizer(session)
    
    action = organizer.add_action("Do something")
    organizer.complete_action(action.id)
    
    assert action.completed


def test_organizer_add_cluster():
    """Test adding clusters."""
    session = BrainstormSession(project_name="test")
    organizer = Organizer(session)
    
    idea1 = organizer.add_idea("Idea 1")
    idea2 = organizer.add_idea("Idea 2")
    
    cluster = organizer.add_cluster(
        "Test Cluster",
        idea_ids=[idea1.id, idea2.id],
        tags=["cluster-tag"]
    )
    
    assert len(session.clusters) == 1
    assert cluster.name == "Test Cluster"
    assert len(cluster.idea_ids) == 2


def test_organizer_delete_idea():
    """Test deleting ideas."""
    session = BrainstormSession(project_name="test")
    organizer = Organizer(session)
    
    idea = organizer.add_idea("Test idea")
    organizer.delete_idea(idea.id, soft=True)
    
    assert idea.merged_into == "deleted"
    assert len(session.get_active_ideas()) == 0


def test_organizer_merge_ideas():
    """Test merging ideas."""
    session = BrainstormSession(project_name="test")
    organizer = Organizer(session)
    
    idea1 = organizer.add_idea("Idea 1", tags=["tag1"])
    idea2 = organizer.add_idea("Idea 2", tags=["tag2"])
    
    organizer.merge_ideas(idea2.id, idea1.id)
    
    assert idea2.merged_into == idea1.id
    assert "tag2" in idea1.tags


def test_get_ideas_by_tag():
    """Test getting ideas by tag."""
    session = BrainstormSession(project_name="test")
    organizer = Organizer(session)
    
    organizer.add_idea("Idea 1", tags=["python"])
    organizer.add_idea("Idea 2", tags=["python", "ai"])
    organizer.add_idea("Idea 3", tags=["ai"])
    
    python_ideas = organizer.get_ideas_by_tag("python")
    assert len(python_ideas) == 2
    
    ai_ideas = organizer.get_ideas_by_tag("ai")
    assert len(ai_ideas) == 2


def test_get_all_tags():
    """Test getting all tags."""
    session = BrainstormSession(project_name="test")
    organizer = Organizer(session)
    
    organizer.add_idea("Idea 1", tags=["python", "ai"])
    organizer.add_idea("Idea 2", tags=["web", "ai"])
    
    tags = organizer.get_all_tags()
    assert set(tags) == {"python", "ai", "web"}


def test_session_serialization():
    """Test full session serialization."""
    session = BrainstormSession(project_name="test")
    organizer = Organizer(session)
    
    organizer.add_idea("Idea 1", tags=["test"])
    organizer.add_action("Action 1")
    organizer.add_cluster("Cluster 1")
    
    # Serialize
    data = session.to_dict()
    
    # Deserialize
    restored = BrainstormSession.from_dict(data)
    
    assert restored.project_name == session.project_name
    assert len(restored.ideas) == 1
    assert len(restored.actions) == 1
    assert len(restored.clusters) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
