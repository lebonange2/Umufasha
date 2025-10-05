"""Organizer for managing brainstorming session state."""
from typing import List, Optional, Dict, Any
from datetime import datetime
from collections import defaultdict

from brain.model import (
    BrainstormSession, Idea, Cluster, ActionItem, 
    TranscriptEntry, Summary, IdeaSource, Priority
)
from brain.dedupe import Deduplicator
from utils.logging import get_logger

logger = get_logger('organizer')


class Organizer:
    """Manages the brainstorming session state and operations."""
    
    def __init__(self, session: BrainstormSession, dedupe_threshold: float = 0.85):
        """Initialize organizer.
        
        Args:
            session: The brainstorming session to manage
            dedupe_threshold: Threshold for deduplication
        """
        self.session = session
        self.deduplicator = Deduplicator(threshold=dedupe_threshold)
        self._tag_index: Dict[str, List[str]] = defaultdict(list)  # tag -> idea_ids
        self._rebuild_indices()
    
    def _rebuild_indices(self):
        """Rebuild internal indices."""
        self._tag_index.clear()
        for idea in self.session.ideas:
            for tag in idea.tags:
                self._tag_index[tag].append(idea.id)
    
    def add_idea(self, text: str, source: IdeaSource = IdeaSource.USER, 
                 tags: Optional[List[str]] = None, **kwargs) -> Idea:
        """Add a new idea to the session.
        
        Args:
            text: Idea text
            source: Source of the idea
            tags: Optional tags
            **kwargs: Additional idea attributes
            
        Returns:
            Created idea
        """
        idea = Idea.create(text=text, source=source, tags=tags or [], **kwargs)
        self.session.ideas.append(idea)
        self.session.updated_at = datetime.now()
        
        # Update indices
        for tag in idea.tags:
            self._tag_index[tag].append(idea.id)
        
        logger.info(f"Added idea {idea.id}: {text[:50]}...")
        return idea
    
    def add_transcript(self, text: str, speaker: str, **kwargs) -> TranscriptEntry:
        """Add a transcript entry.
        
        Args:
            text: Transcript text
            speaker: Speaker ("user" or "assistant")
            **kwargs: Additional attributes
            
        Returns:
            Created transcript entry
        """
        entry = TranscriptEntry.create(text=text, speaker=speaker, **kwargs)
        self.session.transcript.append(entry)
        self.session.updated_at = datetime.now()
        
        logger.debug(f"Added transcript entry from {speaker}")
        return entry
    
    def add_action(self, text: str, priority: Priority = Priority.MEDIUM, 
                   idea_id: Optional[str] = None, **kwargs) -> ActionItem:
        """Add an action item.
        
        Args:
            text: Action text
            priority: Priority level
            idea_id: Related idea ID
            **kwargs: Additional attributes
            
        Returns:
            Created action item
        """
        action = ActionItem.create(text=text, priority=priority, idea_id=idea_id, **kwargs)
        self.session.actions.append(action)
        self.session.updated_at = datetime.now()
        
        logger.info(f"Added action {action.id}: {text[:50]}...")
        return action
    
    def add_cluster(self, name: str, idea_ids: Optional[List[str]] = None, 
                    tags: Optional[List[str]] = None, **kwargs) -> Cluster:
        """Add a cluster.
        
        Args:
            name: Cluster name
            idea_ids: IDs of ideas in this cluster
            tags: Cluster tags
            **kwargs: Additional attributes
            
        Returns:
            Created cluster
        """
        cluster = Cluster.create(
            name=name, 
            idea_ids=idea_ids or [], 
            tags=tags or [],
            **kwargs
        )
        self.session.clusters.append(cluster)
        self.session.updated_at = datetime.now()
        
        logger.info(f"Added cluster {cluster.id}: {name}")
        return cluster
    
    def add_summary(self, text: str, scope: str, idea_ids: Optional[List[str]] = None) -> Summary:
        """Add a summary.
        
        Args:
            text: Summary text
            scope: Scope of summary
            idea_ids: Related idea IDs
            
        Returns:
            Created summary
        """
        summary = Summary.create(text=text, scope=scope, idea_ids=idea_ids or [])
        self.session.summaries.append(summary)
        self.session.updated_at = datetime.now()
        
        logger.info(f"Added summary for scope: {scope}")
        return summary
    
    def tag_idea(self, idea_id: str, tags: List[str]) -> bool:
        """Add tags to an idea.
        
        Args:
            idea_id: Idea ID
            tags: Tags to add
            
        Returns:
            True if successful
        """
        idea = self.session.get_idea(idea_id)
        if not idea:
            logger.warning(f"Idea {idea_id} not found")
            return False
        
        for tag in tags:
            if tag not in idea.tags:
                idea.tags.append(tag)
                self._tag_index[tag].append(idea_id)
        
        self.session.updated_at = datetime.now()
        logger.info(f"Tagged idea {idea_id} with {tags}")
        return True
    
    def promote_idea(self, idea_id: str) -> bool:
        """Mark an idea as key/promoted.
        
        Args:
            idea_id: Idea ID
            
        Returns:
            True if successful
        """
        idea = self.session.get_idea(idea_id)
        if not idea:
            logger.warning(f"Idea {idea_id} not found")
            return False
        
        idea.promoted = True
        self.session.updated_at = datetime.now()
        logger.info(f"Promoted idea {idea_id}")
        return True
    
    def delete_idea(self, idea_id: str, soft: bool = True) -> bool:
        """Delete an idea.
        
        Args:
            idea_id: Idea ID
            soft: If True, mark as merged; if False, remove from list
            
        Returns:
            True if successful
        """
        idea = self.session.get_idea(idea_id)
        if not idea:
            logger.warning(f"Idea {idea_id} not found")
            return False
        
        if soft:
            idea.merged_into = "deleted"
        else:
            self.session.ideas.remove(idea)
            # Clean up indices
            for tag in idea.tags:
                if idea_id in self._tag_index[tag]:
                    self._tag_index[tag].remove(idea_id)
        
        self.session.updated_at = datetime.now()
        logger.info(f"Deleted idea {idea_id} (soft={soft})")
        return True
    
    def complete_action(self, action_id: str, completed: bool = True) -> bool:
        """Mark an action as completed.
        
        Args:
            action_id: Action ID
            completed: Completion status
            
        Returns:
            True if successful
        """
        action = self.session.get_action(action_id)
        if not action:
            logger.warning(f"Action {action_id} not found")
            return False
        
        action.completed = completed
        self.session.updated_at = datetime.now()
        logger.info(f"Action {action_id} completed={completed}")
        return True
    
    def find_duplicates(self) -> List[tuple]:
        """Find duplicate ideas in the session.
        
        Returns:
            List of (idea1_id, idea2_id, similarity) tuples
        """
        active_ideas = self.session.get_active_ideas()
        texts = [idea.text for idea in active_ideas]
        
        duplicates = self.deduplicator.find_duplicates(texts)
        
        # Convert indices to idea IDs
        result = []
        for i, j, similarity in duplicates:
            result.append((active_ideas[i].id, active_ideas[j].id, similarity))
        
        logger.info(f"Found {len(result)} duplicate pairs")
        return result
    
    def merge_ideas(self, source_id: str, target_id: str) -> bool:
        """Merge source idea into target.
        
        Args:
            source_id: ID of idea to merge
            target_id: ID of target idea
            
        Returns:
            True if successful
        """
        source = self.session.get_idea(source_id)
        target = self.session.get_idea(target_id)
        
        if not source or not target:
            logger.warning(f"Cannot merge: source={source_id}, target={target_id}")
            return False
        
        # Mark source as merged
        source.merged_into = target_id
        
        # Merge tags
        for tag in source.tags:
            if tag not in target.tags:
                target.tags.append(tag)
        
        # Update score
        target.score = max(target.score, source.score)
        
        self.session.updated_at = datetime.now()
        logger.info(f"Merged idea {source_id} into {target_id}")
        return True
    
    def search_ideas(self, query: str, top_k: int = 10) -> List[tuple]:
        """Search for ideas matching query.
        
        Args:
            query: Search query
            top_k: Number of results
            
        Returns:
            List of (idea, similarity) tuples
        """
        active_ideas = self.session.get_active_ideas()
        texts = [idea.text for idea in active_ideas]
        
        results = self.deduplicator.find_similar(query, texts, top_k=top_k)
        
        # Convert to idea objects
        return [(active_ideas[i], similarity) for i, similarity in results]
    
    def get_ideas_by_tag(self, tag: str) -> List[Idea]:
        """Get all ideas with a specific tag.
        
        Args:
            tag: Tag to filter by
            
        Returns:
            List of ideas
        """
        idea_ids = self._tag_index.get(tag, [])
        ideas = []
        for idea_id in idea_ids:
            idea = self.session.get_idea(idea_id)
            if idea and idea.merged_into is None:
                ideas.append(idea)
        return ideas
    
    def get_all_tags(self) -> List[str]:
        """Get all unique tags in the session.
        
        Returns:
            List of tags
        """
        return sorted(self._tag_index.keys())
    
    def get_recent_context(self, max_items: int = 10) -> str:
        """Get recent context for LLM prompting.
        
        Args:
            max_items: Maximum number of recent items
            
        Returns:
            Formatted context string
        """
        lines = []
        
        # Recent ideas
        recent_ideas = self.session.get_active_ideas()[-max_items:]
        if recent_ideas:
            lines.append("Recent Ideas:")
            for idea in recent_ideas:
                tags_str = f" [{', '.join(idea.tags)}]" if idea.tags else ""
                lines.append(f"  - {idea.text}{tags_str}")
        
        # Active actions
        active_actions = [a for a in self.session.actions if not a.completed][-5:]
        if active_actions:
            lines.append("\nActive Actions:")
            for action in active_actions:
                lines.append(f"  - [ ] {action.text}")
        
        # Clusters
        if self.session.clusters:
            lines.append("\nClusters:")
            for cluster in self.session.clusters[-5:]:
                lines.append(f"  - {cluster.name} ({len(cluster.idea_ids)} ideas)")
        
        return "\n".join(lines)
