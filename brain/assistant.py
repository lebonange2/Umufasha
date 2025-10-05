"""Brainstorming assistant that coordinates LLM interactions."""
from typing import Optional, Dict, Any
from brain.model import BrainstormSession, IdeaSource, Priority
from brain.organizer import Organizer
from llm.base import LLMBackend, Message
from llm.prompts import (
    SYSTEM_PROMPT, build_brainstorm_prompt, build_clustering_prompt,
    build_summary_prompt, build_action_items_prompt, parse_llm_response
)
from utils.logging import get_logger

logger = get_logger('assistant')


class BrainstormAssistant:
    """AI assistant for brainstorming."""
    
    def __init__(self, llm: LLMBackend, organizer: Organizer):
        """Initialize assistant.
        
        Args:
            llm: LLM backend
            organizer: Session organizer
        """
        self.llm = llm
        self.organizer = organizer
        logger.info("Brainstorm assistant initialized")
    
    def process_user_input(self, user_text: str) -> Optional[str]:
        """Process user input and generate assistant response.
        
        Args:
            user_text: User's transcribed input
            
        Returns:
            Assistant response text
        """
        try:
            # Get recent context
            context = self.organizer.get_recent_context(max_items=10)
            
            # Build prompt
            prompt = build_brainstorm_prompt(user_text, context)
            
            # Get LLM response
            response = self.llm.simple_prompt(SYSTEM_PROMPT, prompt)
            
            if not response:
                logger.warning("No response from LLM")
                return None
            
            # Parse response
            parsed = parse_llm_response(response)
            
            # Add ideas from response
            for idea_text in parsed['ideas']:
                self.organizer.add_idea(
                    text=idea_text,
                    source=IdeaSource.ASSISTANT,
                    tags=parsed['tags'][:3] if parsed['tags'] else []
                )
            
            # Add action items
            for action_text in parsed['actions']:
                self.organizer.add_action(
                    text=action_text,
                    priority=Priority.MEDIUM
                )
            
            logger.info(f"Processed input: {len(parsed['ideas'])} ideas, {len(parsed['actions'])} actions")
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to process input: {e}")
            return None
    
    def generate_clusters(self) -> Optional[str]:
        """Generate clusters from current ideas.
        
        Returns:
            Clustering response text
        """
        try:
            active_ideas = self.organizer.session.get_active_ideas()
            
            if len(active_ideas) < 3:
                logger.info("Not enough ideas to cluster")
                return None
            
            # Build prompt
            idea_texts = [idea.text for idea in active_ideas[-20:]]  # Last 20 ideas
            prompt = build_clustering_prompt(idea_texts)
            
            # Get LLM response
            response = self.llm.simple_prompt(SYSTEM_PROMPT, prompt)
            
            if response:
                logger.info("Generated clusters")
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to generate clusters: {e}")
            return None
    
    def generate_summary(self, scope: str = "session") -> Optional[str]:
        """Generate summary of ideas.
        
        Args:
            scope: Scope of summary ("session", "recent", or "cluster:<id>")
            
        Returns:
            Summary text
        """
        try:
            # Get ideas based on scope
            if scope == "recent":
                ideas = self.organizer.session.get_active_ideas()[-10:]
            elif scope.startswith("cluster:"):
                cluster_id = scope.split(":", 1)[1]
                cluster = self.organizer.session.get_cluster(cluster_id)
                if not cluster:
                    return None
                ideas = [self.organizer.session.get_idea(id) for id in cluster.idea_ids]
                ideas = [i for i in ideas if i and i.merged_into is None]
            else:  # session
                ideas = self.organizer.session.get_active_ideas()
            
            if not ideas:
                logger.info("No ideas to summarize")
                return None
            
            # Build prompt
            idea_texts = [idea.text for idea in ideas]
            prompt = build_summary_prompt(idea_texts, scope)
            
            # Get LLM response
            response = self.llm.simple_prompt(SYSTEM_PROMPT, prompt)
            
            if response:
                # Add summary to session
                self.organizer.add_summary(
                    text=response,
                    scope=scope,
                    idea_ids=[i.id for i in ideas]
                )
                logger.info(f"Generated summary for {scope}")
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to generate summary: {e}")
            return None
    
    def generate_action_items(self, idea_id: str) -> Optional[str]:
        """Generate action items for a specific idea.
        
        Args:
            idea_id: Idea ID
            
        Returns:
            Action items response
        """
        try:
            idea = self.organizer.session.get_idea(idea_id)
            if not idea:
                logger.warning(f"Idea {idea_id} not found")
                return None
            
            # Build prompt
            context = self.organizer.get_recent_context(max_items=5)
            prompt = build_action_items_prompt(idea.text, context)
            
            # Get LLM response
            response = self.llm.simple_prompt(SYSTEM_PROMPT, prompt)
            
            if response:
                # Parse and add actions
                parsed = parse_llm_response(response)
                for action_text in parsed['actions']:
                    self.organizer.add_action(
                        text=action_text,
                        priority=Priority.MEDIUM,
                        idea_id=idea_id
                    )
                
                logger.info(f"Generated {len(parsed['actions'])} action items for idea {idea_id}")
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to generate action items: {e}")
            return None
    
    def auto_tag_idea(self, idea_id: str) -> bool:
        """Automatically generate tags for an idea.
        
        Args:
            idea_id: Idea ID
            
        Returns:
            True if successful
        """
        try:
            idea = self.organizer.session.get_idea(idea_id)
            if not idea or idea.tags:
                return False
            
            # Simple prompt for tagging
            prompt = f"Generate 2-3 relevant tags for this idea: {idea.text}\n\nRespond with only the tags in [tag1, tag2, tag3] format."
            
            response = self.llm.simple_prompt(SYSTEM_PROMPT, prompt)
            
            if response:
                parsed = parse_llm_response(response)
                if parsed['tags']:
                    self.organizer.tag_idea(idea_id, parsed['tags'][:3])
                    logger.info(f"Auto-tagged idea {idea_id}: {parsed['tags']}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to auto-tag idea: {e}")
            return False
    
    def check_duplicates(self) -> Dict[str, Any]:
        """Check for duplicate ideas and suggest merges.
        
        Returns:
            Dictionary with duplicate information
        """
        try:
            duplicates = self.organizer.find_duplicates()
            
            result = {
                'count': len(duplicates),
                'pairs': []
            }
            
            for id1, id2, similarity in duplicates:
                idea1 = self.organizer.session.get_idea(id1)
                idea2 = self.organizer.session.get_idea(id2)
                
                if idea1 and idea2:
                    result['pairs'].append({
                        'id1': id1,
                        'id2': id2,
                        'text1': idea1.text,
                        'text2': idea2.text,
                        'similarity': similarity
                    })
            
            logger.info(f"Found {len(duplicates)} duplicate pairs")
            return result
            
        except Exception as e:
            logger.error(f"Failed to check duplicates: {e}")
            return {'count': 0, 'pairs': []}
