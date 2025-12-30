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
            try:
                GraphRepository.create_project(
                    project_id=project_id,
                    title=project_data.get("title", "Untitled"),
                    genre=None
                )
            except ConnectionError:
                # Neo4j not available - skip sync
                logger.warning(f"Neo4j not available, skipping sync for project {project_id}")
                return
            
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
        except ConnectionError as e:
            logger.warning(f"Neo4j not available, skipping sync for project {project_id}")
        except Exception as e:
            error_msg = str(e)
            if "connection" in error_msg.lower() or "refused" in error_msg.lower() or "ServiceUnavailable" in error_msg:
                logger.warning(f"Neo4j connection issue, skipping sync for project {project_id}")
            else:
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
            
            # Sync characters from character_bible
            if artifacts.get("character_bible"):
                GraphSyncer._sync_characters(project_id, artifacts["character_bible"])
            
            # Sync locations from world_dossier
            if artifacts.get("world_dossier"):
                GraphSyncer._sync_locations(project_id, artifacts["world_dossier"])
            
            # Sync plot arc (plot points, events, acts)
            if artifacts.get("plot_arc"):
                GraphSyncer._sync_plot_arc(project_id, artifacts["plot_arc"])
            
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
            # Support multiple structures: characters, main_characters, supporting_characters
            all_characters = []
            all_characters.extend(character_bible.get("characters", []))
            all_characters.extend(character_bible.get("main_characters", []))
            all_characters.extend(character_bible.get("supporting_characters", []))
            
            for char_data in all_characters:
                if isinstance(char_data, dict):
                    char_name = char_data.get("name", "")
                    if not char_name:
                        continue
                    
                    char_id = char_data.get("id") or f"char_{char_name.lower().replace(' ', '_')}"
                    query = """
                    MATCH (project:Project {id: $project_id})
                    MERGE (char:Character {id: $char_id})
                    SET char.name = $name,
                        char.role = $role,
                        char.occupation = $occupation,
                        char.aliases = $aliases,
                        char.traits = $traits,
                        char.goals = $goals,
                        char.age = $age,
                        char.updatedAt = datetime()
                    MERGE (project)-[:HAS_CHARACTER]->(char)
                    """
                    session.run(
                        query,
                        project_id=project_id,
                        char_id=char_id,
                        name=char_name,
                        role=char_data.get("role", ""),
                        occupation=char_data.get("occupation", ""),
                        aliases=char_data.get("aliases", []),
                        traits=char_data.get("traits", []),
                        goals=char_data.get("goals", []),
                        age=char_data.get("age", None)
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
    
    @staticmethod
    def _sync_plot_arc(project_id: str, plot_arc: Dict[str, Any]):
        """Sync plot arc data (acts, plot points, events, climax) to graph."""
        if not plot_arc:
            return
        
        try:
            with get_neo4j_session() as session:
                story_arc = plot_arc.get("story_arc", {})
                
                # Sync three-act structure
                acts = story_arc.get("three-act_structure", []) or story_arc.get("three_act_structure", [])
                for act_data in acts:
                    if isinstance(act_data, dict):
                        act_name = act_data.get("act", "")
                        if not act_name:
                            continue
                        
                        act_id = f"act_{act_name.lower().replace(' ', '_').replace('-', '_')}"
                        
                        # Create Act node
                        query = """
                        MATCH (project:Project {id: $project_id})
                        MERGE (act:Act {id: $act_id})
                        SET act.name = $name,
                            act.type = $type,
                            act.updatedAt = datetime()
                        MERGE (project)-[:HAS_ACT]->(act)
                        """
                        session.run(
                            query,
                            project_id=project_id,
                            act_id=act_id,
                            name=act_name,
                            type="act"
                        )
                        
                        # Sync events within the act
                        events = act_data.get("events", [])
                        for idx, event_data in enumerate(events):
                            if isinstance(event_data, dict):
                                event_desc = event_data.get("event", "")
                                if event_desc:
                                    event_id = f"{act_id}_event_{idx}"
                                    
                                    query = """
                                    MATCH (act:Act {id: $act_id})
                                    MERGE (event:PlotEvent {id: $event_id})
                                    SET event.description = $description,
                                        event.order = $order,
                                        event.act = $act_name,
                                        event.updatedAt = datetime()
                                    MERGE (act)-[:HAS_EVENT {order: $order}]->(event)
                                    """
                                    session.run(
                                        query,
                                        act_id=act_id,
                                        event_id=event_id,
                                        description=event_desc,
                                        order=idx,
                                        act_name=act_name
                                    )
                
                # Sync key plot points
                plot_points = story_arc.get("key_plot_points", [])
                for idx, point_data in enumerate(plot_points):
                    if isinstance(point_data, dict):
                        point_desc = point_data.get("point", "")
                        if point_desc:
                            point_id = f"plot_point_{idx}"
                            
                            query = """
                            MATCH (project:Project {id: $project_id})
                            MERGE (pp:PlotPoint {id: $point_id})
                            SET pp.description = $description,
                                pp.type = 'key',
                                pp.order = $order,
                                pp.updatedAt = datetime()
                            MERGE (project)-[:HAS_PLOT_POINT {order: $order}]->(pp)
                            """
                            session.run(
                                query,
                                project_id=project_id,
                                point_id=point_id,
                                description=point_desc,
                                order=idx
                            )
                
                # Sync major turning points
                turning_points = story_arc.get("major_turning_points", [])
                for idx, tp_data in enumerate(turning_points):
                    if isinstance(tp_data, dict):
                        tp_desc = tp_data.get("turning_point", "")
                        if tp_desc:
                            tp_id = f"turning_point_{idx}"
                            
                            query = """
                            MATCH (project:Project {id: $project_id})
                            MERGE (tp:TurningPoint {id: $tp_id})
                            SET tp.description = $description,
                                tp.order = $order,
                                tp.updatedAt = datetime()
                            MERGE (project)-[:HAS_TURNING_POINT {order: $order}]->(tp)
                            """
                            session.run(
                                query,
                                project_id=project_id,
                                tp_id=tp_id,
                                description=tp_desc,
                                order=idx
                            )
                
                # Sync climax
                climax = story_arc.get("climax", {})
                if isinstance(climax, dict) and climax.get("event"):
                    climax_desc = climax.get("event", "")
                    
                    query = """
                    MATCH (project:Project {id: $project_id})
                    MERGE (climax:Climax {id: 'climax'})
                    SET climax.description = $description,
                        climax.updatedAt = datetime()
                    MERGE (project)-[:HAS_CLIMAX]->(climax)
                    """
                    session.run(
                        query,
                        project_id=project_id,
                        description=climax_desc
                    )
                
                # Sync resolution
                resolution = story_arc.get("resolution", {})
                if isinstance(resolution, dict):
                    res_events = resolution.get("events", [])
                    if res_events:
                        resolution_desc = " ".join([e.get("event", "") for e in res_events if isinstance(e, dict)])
                        if resolution_desc:
                            query = """
                            MATCH (project:Project {id: $project_id})
                            MERGE (res:Resolution {id: 'resolution'})
                            SET res.description = $description,
                                res.updatedAt = datetime()
                            MERGE (project)-[:HAS_RESOLUTION]->(res)
                            """
                            session.run(
                                query,
                                project_id=project_id,
                                description=resolution_desc
                            )
                
                logger.info(f"Synced plot arc for project {project_id}")
        except Exception as e:
            logger.error(f"Failed to sync plot arc", error=str(e), project_id=project_id)
