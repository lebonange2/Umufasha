"""Sync Book Publishing House project data with Neo4j graph."""
from typing import Dict, Any, List
import structlog
from app.graph.connection import get_neo4j_session
from app.graph.repository import GraphRepository

logger = structlog.get_logger(__name__)


class GraphSyncer:
    """Syncs book project data to/from Neo4j graph."""
    
    @staticmethod
    def sync_project_to_graph(project_id: str, project_data: Dict[str, Any]):
        """Sync project data from Book Publishing House to Neo4j graph."""
        try:
            # Ensure project exists in graph
            GraphRepository.create_project(
                project_id=project_id,
                title=project_data.get("title", "Untitled"),
                genre=None
            )
            
            # Sync characters from character_bible
            if project_data.get("company") and hasattr(project_data["company"], "project"):
                bp = project_data["company"].project
                GraphSyncer._sync_characters(project_id, bp.character_bible)
                GraphSyncer._sync_locations(project_id, bp.world_dossier)
                GraphSyncer._sync_chapters_scenes(project_id, bp.outline, bp.draft_chapters)
            else:
                # Try to sync from artifacts if company not available
                # This happens when syncing from database
                pass
            
            logger.info(f"Synced project {project_id} to graph")
        except Exception as e:
            logger.error(f"Failed to sync project to graph", error=str(e), project_id=project_id)
    
    @staticmethod
    def sync_from_artifacts(project_id: str, artifacts: Dict[str, Any]):
        """Sync directly from artifacts dictionary."""
        try:
            # Ensure project exists
            try:
                GraphRepository.create_project(
                    project_id=project_id,
                    title=artifacts.get("title", "Untitled"),
                    genre=None
                )
            except ConnectionError:
                # Neo4j not available - skip sync
                logger.warning(f"Neo4j not available, skipping sync for project {project_id}")
                return
            
            # Sync characters
            if artifacts.get("character_bible"):
                GraphSyncer._sync_characters(project_id, artifacts["character_bible"])
            
            # Sync locations
            if artifacts.get("world_dossier"):
                GraphSyncer._sync_locations(project_id, artifacts["world_dossier"])
            
            # Sync chapters/scenes
            if artifacts.get("outline"):
                GraphSyncer._sync_chapters_scenes(project_id, artifacts["outline"], artifacts.get("draft_chapters"))
            
            logger.info(f"Synced project {project_id} from artifacts")
        except ConnectionError as e:
            logger.warning(f"Neo4j not available, skipping sync from artifacts for project {project_id}")
        except Exception as e:
            error_msg = str(e)
            if "connection" in error_msg.lower() or "refused" in error_msg.lower() or "ServiceUnavailable" in error_msg:
                logger.warning(f"Neo4j connection issue, skipping sync from artifacts for project {project_id}")
            else:
                logger.error(f"Failed to sync from artifacts", error=str(e), project_id=project_id)
    
    @staticmethod
    def _sync_characters(project_id: str, character_bible: Dict[str, Any]):
        """Sync characters from character_bible to graph."""
        if not character_bible:
            return
        
        with get_neo4j_session() as session:
            characters = character_bible.get("characters", [])
            for char_data in characters:
                if isinstance(char_data, dict):
                    char_id = char_data.get("id") or f"char_{char_data.get('name', '').lower().replace(' ', '_')}"
                    query = """
                    MATCH (project:Project {id: $project_id})
                    MERGE (char:Character {id: $char_id})
                    SET char.name = $name,
                        char.aliases = $aliases,
                        char.traits = $traits,
                        char.goals = $goals,
                        char.updatedAt = datetime()
                    MERGE (project)-[:HAS_CHARACTER]->(char)
                    """
                    session.run(
                        query,
                        project_id=project_id,
                        char_id=char_id,
                        name=char_data.get("name", ""),
                        aliases=char_data.get("aliases", []),
                        traits=char_data.get("traits", []),
                        goals=char_data.get("goals", [])
                    )
    
    @staticmethod
    def _sync_locations(project_id: str, world_dossier: Dict[str, Any]):
        """Sync locations from world_dossier to graph."""
        if not world_dossier:
            return
        
        with get_neo4j_session() as session:
            locations = world_dossier.get("locations", [])
            for loc_data in locations:
                if isinstance(loc_data, dict):
                    loc_id = loc_data.get("id") or f"loc_{loc_data.get('name', '').lower().replace(' ', '_')}"
                    query = """
                    MATCH (project:Project {id: $project_id})
                    MERGE (loc:Location {id: $loc_id})
                    SET loc.name = $name,
                        loc.type = $type,
                        loc.description = $description,
                        loc.updatedAt = datetime()
                    MERGE (project)-[:HAS_LOCATION]->(loc)
                    """
                    session.run(
                        query,
                        project_id=project_id,
                        loc_id=loc_id,
                        name=loc_data.get("name", ""),
                        type=loc_data.get("type", "unknown"),
                        description=loc_data.get("description", "")
                    )
    
    @staticmethod
    def _sync_chapters_scenes(project_id: str, outline: List[Dict[str, Any]], draft_chapters: Dict[int, str]):
        """Sync chapters and scenes from outline to graph."""
        if not outline:
            return
        
        with get_neo4j_session() as session:
            for chapter_data in outline:
                ch_num = chapter_data.get("chapter_number", 0)
                ch_id = chapter_data.get("id") or f"ch_{ch_num}"
                
                # Create/update chapter
                query = """
                MATCH (project:Project {id: $project_id})
                MERGE (ch:Chapter {id: $ch_id})
                SET ch.number = $number,
                    ch.title = $title,
                    ch.synopsis = $synopsis,
                    ch.updatedAt = datetime()
                MERGE (project)-[:HAS_CHAPTER]->(ch)
                """
                session.run(
                    query,
                    project_id=project_id,
                    ch_id=ch_id,
                    number=ch_num,
                    title=chapter_data.get("title", f"Chapter {ch_num}"),
                    synopsis=chapter_data.get("synopsis", "")
                )
                
                # Create/update scenes
                sections = chapter_data.get("sections", [])
                scene_order = 0
                for section in sections:
                    subsections = section.get("subsections", [])
                    for subsection in subsections:
                        scene_order += 1
                        scene_id = f"scene_{ch_num}_{scene_order}"
                        
                        query = """
                        MATCH (ch:Chapter {id: $ch_id})
                        MERGE (s:Scene {id: $scene_id})
                        SET s.title = $title,
                            s.synopsis = $synopsis,
                            s.status = $status,
                            s.order = $order,
                            s.chapterId = $ch_id,
                            s.updatedAt = datetime()
                        MERGE (ch)-[:HAS_SCENE {order: $order}]->(s)
                        """
                        session.run(
                            query,
                            ch_id=ch_id,
                            scene_id=scene_id,
                            title=subsection.get("title", f"Scene {scene_order}"),
                            synopsis="\n".join(subsection.get("main_points", [])),
                            status="outline",
                            order=scene_order,
                        )

