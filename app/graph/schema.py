"""Neo4j schema setup: constraints, indexes, and initial structure."""
from typing import List
import structlog

logger = structlog.get_logger(__name__)

# Try to import Neo4j connection, but don't fail if it's not available
try:
    from app.graph.connection import get_neo4j_session
    NEO4J_AVAILABLE = True
except (ImportError, Exception):
    NEO4J_AVAILABLE = False
    logger.info("Neo4j not available, schema operations will be skipped")


# Node labels
NODE_LABELS = [
    "Project",
    "Character",
    "Location",
    "Environment",
    "Faction",
    "Artifact",
    "Concept",
    "Rule",
    "Theme",
    "Chapter",
    "Scene",
    "Event",
    "Issue",
    "Source",
    "Command",  # For undo/redo
    "Layout",   # For saved layouts
    "Act",      # Story acts (beginning, middle, end)
    "PlotEvent",  # Events within acts
    "PlotPoint",  # Key plot points
    "TurningPoint",  # Major turning points
    "Climax",   # Story climax
    "Resolution",  # Story resolution
    "Constraint",  # Story constraints
    "SuccessCriterion",  # Success criteria
]

# Relationship types
RELATIONSHIP_TYPES = [
    "HAS_CHARACTER",
    "HAS_LOCATION",
    "HAS_SCENE",
    "HAS_CHAPTER",
    "HAS_ENVIRONMENT",
    "HAS_FACTION",
    "HAS_ARTIFACT",
    "HAS_CONCEPT",
    "HAS_RULE",
    "HAS_THEME",
    "HAS_EVENT",
    "HAS_ISSUE",
    "HAS_SOURCE",
    "HAS_COMMAND",
    "HAS_SCENE",
    "OCCURS_IN",
    "USES_ENVIRONMENT",
    "APPEARS_IN",
    "KNOWS",
    "MENTORS",
    "LOVES",
    "HATES",
    "RIVALS",
    "ALLY_OF",
    "ENEMY_OF",
    "PRECEDES",
    "HAPPENS_IN",
    "CONTAINS_EVENT",
    "DEFINED_IN",
    "SUPPORTED_BY",
    "EXPRESSED_IN",
    "SAVED_LAYOUT",
    "HAS_ACT",
    "HAS_PLOT_POINT",
    "HAS_TURNING_POINT",
    "HAS_CLIMAX",
    "HAS_RESOLUTION",
    "HAS_CONSTRAINT",
    "HAS_SUCCESS_CRITERION",
]

# Allowed relationship combinations (source_label -> relationship_type -> target_label)
ALLOWED_RELATIONSHIPS = {
    "Project": {
        "HAS_CHARACTER": ["Character"],
        "HAS_LOCATION": ["Location"],
        "HAS_SCENE": ["Scene"],
        "HAS_CHAPTER": ["Chapter"],
        "HAS_ENVIRONMENT": ["Environment"],
        "HAS_FACTION": ["Faction"],
        "HAS_ARTIFACT": ["Artifact"],
        "HAS_CONCEPT": ["Concept"],
        "HAS_RULE": ["Rule"],
        "HAS_THEME": ["Theme"],
        "HAS_EVENT": ["Event"],
        "HAS_ISSUE": ["Issue"],
        "HAS_SOURCE": ["Source"],
        "HAS_COMMAND": ["Command"],
        "HAS_ACT": ["Act"],
        "HAS_PLOT_POINT": ["PlotPoint"],
        "HAS_TURNING_POINT": ["TurningPoint"],
        "HAS_CLIMAX": ["Climax"],
        "HAS_RESOLUTION": ["Resolution"],
        "HAS_CONSTRAINT": ["Constraint"],
        "HAS_SUCCESS_CRITERION": ["SuccessCriterion"],
    },
    "Act": {
        "HAS_EVENT": ["PlotEvent"],
    },
    "Chapter": {
        "HAS_SCENE": ["Scene"],
    },
    "Scene": {
        "OCCURS_IN": ["Location"],
        "USES_ENVIRONMENT": ["Environment"],
        "CONTAINS_EVENT": ["Event"],
        "EXPRESSED_IN": ["Theme"],
    },
    "Character": {
        "APPEARS_IN": ["Scene"],
        "KNOWS": ["Character"],
        "MENTORS": ["Character"],
        "LOVES": ["Character"],
        "HATES": ["Character"],
        "RIVALS": ["Character"],
        "ALLY_OF": ["Character"],
        "ENEMY_OF": ["Character"],
    },
    "Scene": {
        "PRECEDES": ["Scene"],
    },
    "Event": {
        "HAPPENS_IN": ["Location"],
    },
    "Concept": {
        "DEFINED_IN": ["Chapter", "Scene"],
    },
    "Source": {
        "SUPPORTED_BY": ["Concept", "Rule", "Event"],
    },
    "Issue": {
        "HAS_ISSUE": ["Character", "Location", "Scene", "Chapter", "Event"],
    },
}


def create_constraints_and_indexes():
    """Create all constraints and indexes for the graph schema."""
    if not NEO4J_AVAILABLE:
        logger.info("Neo4j not available, skipping schema initialization")
        return
    
    with get_neo4j_session() as session:
        constraints = [
            # Unique constraints on id property for each label
            "CREATE CONSTRAINT project_id_unique IF NOT EXISTS FOR (p:Project) REQUIRE p.id IS UNIQUE",
            "CREATE CONSTRAINT character_id_unique IF NOT EXISTS FOR (c:Character) REQUIRE c.id IS UNIQUE",
            "CREATE CONSTRAINT location_id_unique IF NOT EXISTS FOR (l:Location) REQUIRE l.id IS UNIQUE",
            "CREATE CONSTRAINT environment_id_unique IF NOT EXISTS FOR (e:Environment) REQUIRE e.id IS UNIQUE",
            "CREATE CONSTRAINT faction_id_unique IF NOT EXISTS FOR (f:Faction) REQUIRE f.id IS UNIQUE",
            "CREATE CONSTRAINT artifact_id_unique IF NOT EXISTS FOR (a:Artifact) REQUIRE a.id IS UNIQUE",
            "CREATE CONSTRAINT concept_id_unique IF NOT EXISTS FOR (c:Concept) REQUIRE c.id IS UNIQUE",
            "CREATE CONSTRAINT rule_id_unique IF NOT EXISTS FOR (r:Rule) REQUIRE r.id IS UNIQUE",
            "CREATE CONSTRAINT theme_id_unique IF NOT EXISTS FOR (t:Theme) REQUIRE t.id IS UNIQUE",
            "CREATE CONSTRAINT chapter_id_unique IF NOT EXISTS FOR (ch:Chapter) REQUIRE ch.id IS UNIQUE",
            "CREATE CONSTRAINT scene_id_unique IF NOT EXISTS FOR (s:Scene) REQUIRE s.id IS UNIQUE",
            "CREATE CONSTRAINT event_id_unique IF NOT EXISTS FOR (e:Event) REQUIRE e.id IS UNIQUE",
            "CREATE CONSTRAINT issue_id_unique IF NOT EXISTS FOR (i:Issue) REQUIRE i.id IS UNIQUE",
            "CREATE CONSTRAINT source_id_unique IF NOT EXISTS FOR (s:Source) REQUIRE s.id IS UNIQUE",
            "CREATE CONSTRAINT command_id_unique IF NOT EXISTS FOR (c:Command) REQUIRE c.id IS UNIQUE",
            "CREATE CONSTRAINT act_id_unique IF NOT EXISTS FOR (a:Act) REQUIRE a.id IS UNIQUE",
            "CREATE CONSTRAINT plotevent_id_unique IF NOT EXISTS FOR (pe:PlotEvent) REQUIRE pe.id IS UNIQUE",
            "CREATE CONSTRAINT plotpoint_id_unique IF NOT EXISTS FOR (pp:PlotPoint) REQUIRE pp.id IS UNIQUE",
            "CREATE CONSTRAINT turningpoint_id_unique IF NOT EXISTS FOR (tp:TurningPoint) REQUIRE tp.id IS UNIQUE",
            "CREATE CONSTRAINT climax_id_unique IF NOT EXISTS FOR (c:Climax) REQUIRE c.id IS UNIQUE",
            "CREATE CONSTRAINT resolution_id_unique IF NOT EXISTS FOR (r:Resolution) REQUIRE r.id IS UNIQUE",
            "CREATE CONSTRAINT constraint_id_unique IF NOT EXISTS FOR (c:Constraint) REQUIRE c.id IS UNIQUE",
            "CREATE CONSTRAINT successcriterion_id_unique IF NOT EXISTS FOR (sc:SuccessCriterion) REQUIRE sc.id IS UNIQUE",
        ]
        
        indexes = [
            # Fulltext indexes for search
            "CREATE FULLTEXT INDEX character_name_fulltext IF NOT EXISTS FOR (c:Character) ON EACH [c.name, c.aliases]",
            "CREATE FULLTEXT INDEX location_name_fulltext IF NOT EXISTS FOR (l:Location) ON EACH [l.name, l.description]",
            "CREATE FULLTEXT INDEX scene_title_fulltext IF NOT EXISTS FOR (s:Scene) ON EACH [s.title, s.synopsis]",
            "CREATE FULLTEXT INDEX chapter_title_fulltext IF NOT EXISTS FOR (ch:Chapter) ON EACH [ch.title, ch.synopsis]",
            "CREATE FULLTEXT INDEX concept_name_fulltext IF NOT EXISTS FOR (c:Concept) ON EACH [c.name, c.definition]",
            
            # Property indexes for common queries
            "CREATE INDEX scene_status_index IF NOT EXISTS FOR (s:Scene) ON (s.status)",
            "CREATE INDEX scene_chapter_index IF NOT EXISTS FOR (s:Scene) ON (s.chapterId)",
            "CREATE INDEX chapter_number_index IF NOT EXISTS FOR (ch:Chapter) ON (ch.number)",
            "CREATE INDEX event_time_index IF NOT EXISTS FOR (e:Event) ON (e.time)",
            "CREATE INDEX issue_severity_index IF NOT EXISTS FOR (i:Issue) ON (i.severity)",
        ]
        
        # Execute constraints
        for constraint in constraints:
            try:
                session.run(constraint)
                logger.info("Created constraint", constraint=constraint[:50])
            except Exception as e:
                # Constraint might already exist
                logger.debug("Constraint creation result", constraint=constraint[:50], error=str(e))
        
        # Execute indexes
        for index in indexes:
            try:
                session.run(index)
                logger.info("Created index", index=index[:50])
            except Exception as e:
                # Index might already exist
                logger.debug("Index creation result", index=index[:50], error=str(e))
        
        logger.info("Schema setup completed")


def validate_relationship(source_label: str, rel_type: str, target_label: str) -> bool:
    """Validate if a relationship is allowed between two node types."""
    allowed_targets = ALLOWED_RELATIONSHIPS.get(source_label, {}).get(rel_type, [])
    return target_label in allowed_targets


if __name__ == "__main__":
    # Run schema setup
    create_constraints_and_indexes()

