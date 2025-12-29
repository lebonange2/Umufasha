"""Render manuscript from graph state."""
from typing import Dict, Any, List, Optional
from neo4j import Session
import structlog
from app.graph.connection import get_neo4j_session

logger = structlog.get_logger(__name__)


class GraphRenderer:
    """Renders book manuscript from graph."""
    
    @staticmethod
    def render_manuscript(project_id: str) -> Dict[str, Any]:
        """Render complete manuscript from graph."""
        with get_neo4j_session() as session:
            # Get project
            project = GraphRenderer._get_project(session, project_id)
            if not project:
                raise ValueError(f"Project not found: {project_id}")
            
            # Build outline structure
            outline = GraphRenderer._build_outline(session, project_id)
            
            # Generate markdown
            markdown = GraphRenderer._generate_markdown(project, outline)
            
            return {
                "project_id": project_id,
                "title": project.get("title", "Untitled"),
                "outline": outline,
                "markdown": markdown,
                "word_count": len(markdown.split())
            }
    
    @staticmethod
    def _get_project(session: Session, project_id: str) -> Optional[Dict[str, Any]]:
        """Get project node."""
        query = """
        MATCH (p:Project {id: $project_id})
        RETURN p
        """
        result = session.run(query, project_id=project_id)
        record = result.single()
        if record:
            return dict(record["p"])
        return None
    
    @staticmethod
    def _build_outline(session: Session, project_id: str) -> List[Dict[str, Any]]:
        """Build outline structure from graph."""
        query = """
        MATCH (project:Project {id: $project_id})-[:HAS_CHAPTER]->(ch:Chapter)
        OPTIONAL MATCH (ch)-[has_scene:HAS_SCENE]->(s:Scene)
        OPTIONAL MATCH (s)-[:OCCURS_IN]->(l:Location)
        OPTIONAL MATCH (s)-[:USES_ENVIRONMENT]->(e:Environment)
        OPTIONAL MATCH (c:Character)-[:APPEARS_IN]->(s)
        OPTIONAL MATCH (event:Event)-[:HAPPENS_IN]->(s)
        OPTIONAL MATCH (theme:Theme)-[:EXPRESSED_IN]->(s)
        WITH ch, has_scene, s, l, e, 
             collect(DISTINCT c) as characters,
             collect(DISTINCT event) as events,
             collect(DISTINCT theme) as themes
        ORDER BY ch.number, has_scene.order
        WITH ch, collect({
            id: s.id,
            title: s.title,
            synopsis: s.synopsis,
            status: s.status,
            order: has_scene.order,
            pov: s.pov,
            timeStart: s.timeStart,
            timeEnd: s.timeEnd,
            location: l.name,
            environment: e.name,
            characters: [char in characters WHERE char IS NOT NULL | {id: char.id, name: char.name}],
            events: [ev in events WHERE ev IS NOT NULL | {id: ev.id, name: ev.name}],
            themes: [th in themes WHERE th IS NOT NULL | {id: th.id, name: th.name}]
        }) as scenes
        ORDER BY ch.number
        RETURN {
            id: ch.id,
            number: ch.number,
            title: ch.title,
            synopsis: ch.synopsis,
            scenes: scenes
        } as chapter
        """
        result = session.run(query, project_id=project_id)
        chapters = []
        for record in result:
            chapters.append(record["chapter"])
        return chapters
    
    @staticmethod
    def _generate_markdown(project: Dict[str, Any], outline: List[Dict[str, Any]]) -> str:
        """Generate markdown from outline."""
        lines = []
        
        # Title
        title = project.get("title", "Untitled Book")
        lines.append(f"# {title}")
        lines.append("")
        
        # Table of Contents
        lines.append("## Table of Contents")
        lines.append("")
        for chapter in outline:
            ch_num = chapter.get("number", 0)
            ch_title = chapter.get("title", f"Chapter {ch_num}")
            lines.append(f"{ch_num}. [{ch_title}](#chapter-{ch_num})")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # Chapters
        for chapter in outline:
            ch_num = chapter.get("number", 0)
            ch_title = chapter.get("title", f"Chapter {ch_num}")
            ch_synopsis = chapter.get("synopsis", "")
            scenes = chapter.get("scenes", [])
            
            lines.append(f"## Chapter {ch_num}: {ch_title}")
            lines.append("")
            if ch_synopsis:
                lines.append(f"*{ch_synopsis}*")
                lines.append("")
            
            # Scenes
            for scene in scenes:
                if not scene or not scene.get("id"):
                    continue
                
                scene_title = scene.get("title", "Untitled Scene")
                scene_synopsis = scene.get("synopsis", "")
                scene_status = scene.get("status", "draft")
                location = scene.get("location")
                environment = scene.get("environment")
                characters = scene.get("characters", [])
                events = scene.get("events", [])
                themes = scene.get("themes", [])
                pov = scene.get("pov")
                time_start = scene.get("timeStart")
                time_end = scene.get("timeEnd")
                
                lines.append(f"### {scene_title}")
                lines.append("")
                
                # Scene metadata (as comments)
                metadata = []
                if location:
                    metadata.append(f"Location: {location}")
                if environment:
                    metadata.append(f"Environment: {environment}")
                if pov:
                    metadata.append(f"POV: {pov}")
                if time_start or time_end:
                    time_str = f"{time_start or '?'} - {time_end or '?'}"
                    metadata.append(f"Time: {time_str}")
                if characters:
                    char_names = [c.get("name", "Unknown") for c in characters]
                    metadata.append(f"Characters: {', '.join(char_names)}")
                if events:
                    event_names = [e.get("name", "Unknown") for e in events]
                    metadata.append(f"Events: {', '.join(event_names)}")
                if themes:
                    theme_names = [t.get("name", "Unknown") for t in themes]
                    metadata.append(f"Themes: {', '.join(theme_names)}")
                
                if metadata:
                    lines.append("<!--")
                    for meta in metadata:
                        lines.append(f"  {meta}")
                    lines.append(f"  Status: {scene_status}")
                    lines.append("-->")
                    lines.append("")
                
                # Scene content
                if scene_synopsis:
                    lines.append(scene_synopsis)
                    lines.append("")
                
                if scene_status == "draft":
                    lines.append("*[Draft content to be generated]*")
                    lines.append("")
                elif scene_status == "idea":
                    lines.append("*[Scene idea - outline pending]*")
                    lines.append("")
                else:
                    # If scene has full content, it would be stored in properties
                    lines.append("*[Scene content]*")
                    lines.append("")
            
            lines.append("")
            lines.append("---")
            lines.append("")
        
        return "\n".join(lines)

