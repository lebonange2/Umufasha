"""Graph validation and continuity checking."""
from typing import List, Dict, Any
from neo4j import Session
import structlog
from app.graph.connection import get_neo4j_session

logger = structlog.get_logger(__name__)


class ValidationIssue:
    """Represents a validation issue."""
    def __init__(self, type: str, severity: str, description: str, node_ids: List[str] = None):
        self.type = type
        self.severity = severity  # "error", "warning", "info"
        self.description = description
        self.node_ids = node_ids or []
    
    def to_dict(self):
        return {
            "type": self.type,
            "severity": self.severity,
            "description": self.description,
            "node_ids": self.node_ids
        }


class GraphValidator:
    """Validates graph consistency and continuity."""
    
    @staticmethod
    def validate_project(project_id: str) -> List[Dict[str, Any]]:
        """Run all validation checks on a project."""
        issues = []
        
        with get_neo4j_session() as session:
            # Check 1: Orphan scenes (not attached to any chapter)
            issues.extend(GraphValidator._check_orphan_scenes(session, project_id))
            
            # Check 2: Scenes missing location
            issues.extend(GraphValidator._check_scenes_missing_location(session, project_id))
            
            # Check 3: Cycles in PRECEDES relationships
            issues.extend(GraphValidator._check_precedes_cycles(session, project_id))
            
            # Check 4: Character appears in overlapping scenes at different locations
            issues.extend(GraphValidator._check_character_location_conflicts(session, project_id))
            
            # Check 5: Undefined concepts used but not defined
            issues.extend(GraphValidator._check_undefined_concepts(session, project_id))
            
            # Check 6: Duplicate entities (same name, different ids)
            issues.extend(GraphValidator._check_duplicate_entities(session, project_id))
        
        return [issue.to_dict() for issue in issues]
    
    @staticmethod
    def _check_orphan_scenes(session: Session, project_id: str) -> List[ValidationIssue]:
        """Check for scenes not attached to any chapter."""
        query = """
        MATCH (project:Project {id: $project_id})-[:HAS_SCENE]->(s:Scene)
        WHERE NOT (s)<-[:HAS_SCENE]-(:Chapter)
        RETURN s.id as scene_id, s.title as title
        """
        result = session.run(query, project_id=project_id)
        issues = []
        for record in result:
            issues.append(ValidationIssue(
                type="orphan_scene",
                severity="error",
                description=f"Scene '{record['title']}' is not attached to any chapter",
                node_ids=[record["scene_id"]]
            ))
        return issues
    
    @staticmethod
    def _check_scenes_missing_location(session: Session, project_id: str) -> List[ValidationIssue]:
        """Check for scenes without OCCURS_IN location."""
        query = """
        MATCH (project:Project {id: $project_id})-[:HAS_SCENE]->(s:Scene)
        WHERE NOT (s)-[:OCCURS_IN]->(:Location)
        RETURN s.id as scene_id, s.title as title
        """
        result = session.run(query, project_id=project_id)
        issues = []
        for record in result:
            issues.append(ValidationIssue(
                type="missing_location",
                severity="warning",
                description=f"Scene '{record['title']}' does not have a location",
                node_ids=[record["scene_id"]]
            ))
        return issues
    
    @staticmethod
    def _check_precedes_cycles(session: Session, project_id: str) -> List[ValidationIssue]:
        """Check for cycles in PRECEDES relationships."""
        query = """
        MATCH (project:Project {id: $project_id})-[:HAS_SCENE]->(s:Scene)
        MATCH path = (s)-[:PRECEDES*]->(s)
        RETURN [n in nodes(path) | n.id] as cycle
        LIMIT 10
        """
        result = session.run(query, project_id=project_id)
        issues = []
        for record in result:
            cycle = record["cycle"]
            issues.append(ValidationIssue(
                type="precedes_cycle",
                severity="error",
                description=f"Cycle detected in PRECEDES relationships: {' -> '.join(cycle)}",
                node_ids=cycle
            ))
        return issues
    
    @staticmethod
    def _check_character_location_conflicts(session: Session, project_id: str) -> List[ValidationIssue]:
        """Check if character appears in overlapping scenes at different locations."""
        query = """
        MATCH (project:Project {id: $project_id})-[:HAS_CHARACTER]->(c:Character)
        MATCH (c)-[:APPEARS_IN]->(s1:Scene)-[:OCCURS_IN]->(l1:Location)
        MATCH (c)-[:APPEARS_IN]->(s2:Scene)-[:OCCURS_IN]->(l2:Location)
        WHERE s1 <> s2 
          AND s1.timeStart IS NOT NULL 
          AND s2.timeStart IS NOT NULL
          AND s1.timeEnd IS NOT NULL 
          AND s2.timeEnd IS NOT NULL
          AND l1 <> l2
          AND (
            (s1.timeStart <= s2.timeStart AND s1.timeEnd > s2.timeStart) OR
            (s2.timeStart <= s1.timeStart AND s2.timeEnd > s1.timeStart)
          )
        RETURN c.id as char_id, c.name as char_name, 
               s1.id as scene1_id, s1.title as scene1_title, l1.name as loc1,
               s2.id as scene2_id, s2.title as scene2_title, l2.name as loc2
        """
        result = session.run(query, project_id=project_id)
        issues = []
        for record in result:
            issues.append(ValidationIssue(
                type="character_location_conflict",
                severity="error",
                description=f"Character '{record['char_name']}' appears in overlapping scenes at different locations: '{record['scene1_title']}' ({record['loc1']}) and '{record['scene2_title']}' ({record['loc2']})",
                node_ids=[record["char_id"], record["scene1_id"], record["scene2_id"]]
            ))
        return issues
    
    @staticmethod
    def _check_undefined_concepts(session: Session, project_id: str) -> List[ValidationIssue]:
        """Check for concepts referenced but not defined."""
        # This is a simplified check - in practice, you'd track concept usage
        query = """
        MATCH (project:Project {id: $project_id})-[:HAS_CONCEPT]->(c:Concept)
        WHERE c.definition IS NULL OR c.definition = ""
        RETURN c.id as concept_id, c.name as concept_name
        """
        result = session.run(query, project_id=project_id)
        issues = []
        for record in result:
            issues.append(ValidationIssue(
                type="undefined_concept",
                severity="warning",
                description=f"Concept '{record['concept_name']}' has no definition",
                node_ids=[record["concept_id"]]
            ))
        return issues
    
    @staticmethod
    def _check_duplicate_entities(session: Session, project_id: str) -> List[ValidationIssue]:
        """Check for duplicate entities with same name but different ids."""
        # Check characters
        query = """
        MATCH (project:Project {id: $project_id})-[:HAS_CHARACTER]->(c:Character)
        WITH c.name as name, collect(c.id) as ids
        WHERE size(ids) > 1
        RETURN name, ids
        """
        result = session.run(query, project_id=project_id)
        issues = []
        for record in result:
            issues.append(ValidationIssue(
                type="duplicate_character",
                severity="warning",
                description=f"Multiple characters with name '{record['name']}' found. Consider merging.",
                node_ids=record["ids"]
            ))
        return issues

