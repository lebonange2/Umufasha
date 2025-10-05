"""Core data models for brainstorming session."""
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
import uuid


class IdeaSource(str, Enum):
    """Source of an idea."""
    USER = "user"
    ASSISTANT = "assistant"


class Priority(str, Enum):
    """Priority levels for action items."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class Idea:
    """Represents a single idea or thought."""
    id: str
    text: str
    tags: List[str] = field(default_factory=list)
    source: IdeaSource = IdeaSource.USER
    score: float = 0.0  # Importance/relevance score
    timestamp: datetime = field(default_factory=datetime.now)
    parent_id: Optional[str] = None  # For idea variations
    merged_into: Optional[str] = None  # If deduplicated
    promoted: bool = False  # Key idea flag
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['source'] = self.source.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Idea':
        """Create from dictionary."""
        data = data.copy()
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        data['source'] = IdeaSource(data['source'])
        return cls(**data)
    
    @classmethod
    def create(cls, text: str, source: IdeaSource = IdeaSource.USER, **kwargs) -> 'Idea':
        """Factory method to create a new idea."""
        return cls(
            id=str(uuid.uuid4())[:8],
            text=text,
            source=source,
            **kwargs
        )


@dataclass
class Cluster:
    """Represents a thematic cluster of ideas."""
    id: str
    name: str
    tags: List[str] = field(default_factory=list)
    idea_ids: List[str] = field(default_factory=list)
    description: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Cluster':
        """Create from dictionary."""
        data = data.copy()
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)
    
    @classmethod
    def create(cls, name: str, **kwargs) -> 'Cluster':
        """Factory method to create a new cluster."""
        return cls(
            id=str(uuid.uuid4())[:8],
            name=name,
            **kwargs
        )


@dataclass
class ActionItem:
    """Represents an action item or todo."""
    id: str
    text: str
    completed: bool = False
    priority: Priority = Priority.MEDIUM
    due_date: Optional[datetime] = None
    idea_id: Optional[str] = None  # Related idea
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['priority'] = self.priority.value
        if self.due_date:
            data['due_date'] = self.due_date.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ActionItem':
        """Create from dictionary."""
        data = data.copy()
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        data['priority'] = Priority(data['priority'])
        if data.get('due_date'):
            data['due_date'] = datetime.fromisoformat(data['due_date'])
        return cls(**data)
    
    @classmethod
    def create(cls, text: str, **kwargs) -> 'ActionItem':
        """Factory method to create a new action item."""
        return cls(
            id=str(uuid.uuid4())[:8],
            text=text,
            **kwargs
        )


@dataclass
class TranscriptEntry:
    """Represents a transcript entry."""
    id: str
    text: str
    speaker: str  # "user" or "assistant"
    timestamp: datetime = field(default_factory=datetime.now)
    audio_duration: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TranscriptEntry':
        """Create from dictionary."""
        data = data.copy()
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)
    
    @classmethod
    def create(cls, text: str, speaker: str, **kwargs) -> 'TranscriptEntry':
        """Factory method to create a new transcript entry."""
        return cls(
            id=str(uuid.uuid4())[:8],
            text=text,
            speaker=speaker,
            **kwargs
        )


@dataclass
class Summary:
    """Represents a summary of ideas or session."""
    id: str
    text: str
    scope: str  # "session", "cluster:<id>", "recent"
    timestamp: datetime = field(default_factory=datetime.now)
    idea_ids: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Summary':
        """Create from dictionary."""
        data = data.copy()
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)
    
    @classmethod
    def create(cls, text: str, scope: str, **kwargs) -> 'Summary':
        """Factory method to create a new summary."""
        return cls(
            id=str(uuid.uuid4())[:8],
            text=text,
            scope=scope,
            **kwargs
        )


@dataclass
class BrainstormSession:
    """Complete brainstorming session state."""
    project_name: str
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    ideas: List[Idea] = field(default_factory=list)
    clusters: List[Cluster] = field(default_factory=list)
    actions: List[ActionItem] = field(default_factory=list)
    transcript: List[TranscriptEntry] = field(default_factory=list)
    summaries: List[Summary] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'project_name': self.project_name,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'ideas': [idea.to_dict() for idea in self.ideas],
            'clusters': [cluster.to_dict() for cluster in self.clusters],
            'actions': [action.to_dict() for action in self.actions],
            'transcript': [entry.to_dict() for entry in self.transcript],
            'summaries': [summary.to_dict() for summary in self.summaries],
            'metadata': self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BrainstormSession':
        """Create from dictionary."""
        return cls(
            project_name=data['project_name'],
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at']),
            ideas=[Idea.from_dict(i) for i in data.get('ideas', [])],
            clusters=[Cluster.from_dict(c) for c in data.get('clusters', [])],
            actions=[ActionItem.from_dict(a) for a in data.get('actions', [])],
            transcript=[TranscriptEntry.from_dict(t) for t in data.get('transcript', [])],
            summaries=[Summary.from_dict(s) for s in data.get('summaries', [])],
            metadata=data.get('metadata', {}),
        )
    
    def get_idea(self, idea_id: str) -> Optional[Idea]:
        """Get idea by ID."""
        for idea in self.ideas:
            if idea.id == idea_id:
                return idea
        return None
    
    def get_cluster(self, cluster_id: str) -> Optional[Cluster]:
        """Get cluster by ID."""
        for cluster in self.clusters:
            if cluster.id == cluster_id:
                return cluster
        return None
    
    def get_action(self, action_id: str) -> Optional[ActionItem]:
        """Get action by ID."""
        for action in self.actions:
            if action.id == action_id:
                return action
        return None
    
    def get_active_ideas(self) -> List[Idea]:
        """Get all non-merged ideas."""
        return [idea for idea in self.ideas if idea.merged_into is None]
    
    def get_key_ideas(self) -> List[Idea]:
        """Get promoted/key ideas."""
        return [idea for idea in self.get_active_ideas() if idea.promoted]
