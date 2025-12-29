"""Neo4j Knowledge Graph API routes."""
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
import structlog
import uuid

from app.graph.repository import GraphRepository
from app.graph.validation import GraphValidator
from app.graph.renderer import GraphRenderer
from app.graph.commands import CommandLog
from app.graph.schema import NODE_LABELS, RELATIONSHIP_TYPES, ALLOWED_RELATIONSHIPS
from app.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

router = APIRouter()


# Pydantic models
class NodeCreate(BaseModel):
    labels: List[str]
    properties: Dict[str, Any]


class NodeUpdate(BaseModel):
    properties: Dict[str, Any]


class RelationshipCreate(BaseModel):
    source_id: str
    target_id: str
    rel_type: str
    properties: Optional[Dict[str, Any]] = None


class RelationshipUpdate(BaseModel):
    properties: Dict[str, Any]


@router.post("/api/projects/{project_id}/graph/init")
async def init_project_graph(
    project_id: str, 
    title: Optional[str] = Query("Untitled"),
    genre: Optional[str] = Query(None)
):
    """Initialize graph for a project."""
    try:
        # Check if project already exists
        try:
            existing = GraphRepository.get_subgraph(project_id, depth=0)
            if existing.get("nodes") and len(existing["nodes"]) > 0:
                # Project already exists
                return {"success": True, "message": "Project already initialized", "node": existing["nodes"][0]}
        except ConnectionError:
            # Neo4j is not available - return success but indicate Neo4j is unavailable
            logger.warning(f"Neo4j not available, cannot check if project exists: {project_id}")
            return {
                "success": True, 
                "message": "Neo4j is not available. Graph will be initialized when Neo4j is available.",
                "neo4j_unavailable": True
            }
        except Exception:
            # Project doesn't exist, continue to create
            pass
        
        try:
            node = GraphRepository.create_project(project_id, title or "Untitled", genre)
            return {"success": True, "node": node}
        except ConnectionError as e:
            # Neo4j is not available - return success but indicate Neo4j is unavailable
            logger.warning(f"Neo4j not available, cannot create project node: {project_id}")
            return {
                "success": True, 
                "message": "Neo4j is not available. Graph will be initialized when Neo4j is available.",
                "neo4j_unavailable": True
            }
    except Exception as e:
        error_msg = str(e)
        logger.error("Failed to initialize project graph", error=error_msg, project_id=project_id, exc_info=True)
        
        # If it's a connection error, return success with a message instead of raising
        if ("connection" in error_msg.lower() or 
            "neo4j" in error_msg.lower() or 
            "ConnectionError" in error_msg or
            "ServiceUnavailable" in error_msg):
            return {
                "success": True, 
                "message": "Neo4j is not available. Graph will be initialized when Neo4j is available.",
                "neo4j_unavailable": True
            }
        
        raise HTTPException(status_code=500, detail=f"Failed to initialize graph: {error_msg}")


@router.get("/api/projects/{project_id}/graph")
async def get_subgraph(
    project_id: str,
    focus_node_id: Optional[str] = Query(None),
    depth: int = Query(2, ge=0, le=5),
    labels: Optional[str] = Query(None),
    stage: Optional[str] = Query(None),
    chapter: Optional[int] = Query(None)
):
    """Fetch subgraph."""
    try:
        label_list = labels.split(",") if labels else None
        result = GraphRepository.get_subgraph(
            project_id=project_id,
            focus_node_id=focus_node_id,
            depth=depth,
            labels=label_list,
            stage=stage,
            chapter=chapter
        )
        return result
    except Exception as e:
        error_msg = str(e)
        logger.error("Failed to fetch subgraph", error=error_msg, project_id=project_id, exc_info=True)
        
        # If project doesn't exist in Neo4j, try to initialize it
        if "not found" in error_msg.lower() or "does not exist" in error_msg.lower():
            try:
                # Try to get project info from Book Publishing House
                from app.database import get_db
                from sqlalchemy.ext.asyncio import AsyncSession
                from sqlalchemy import select
                from app.models import BookPublishingHouseProject as BPHProject
                
                # We can't use Depends here, so we'll just return empty graph
                # The frontend will handle initialization
                logger.warning(f"Project {project_id} not found in Neo4j, returning empty graph")
                return {"nodes": [], "edges": []}
            except Exception as init_err:
                logger.error("Failed to initialize missing project", error=str(init_err))
        
        # For connection errors, return empty graph instead of failing
        if ("connection" in error_msg.lower() or 
            "neo4j" in error_msg.lower() or 
            "ConnectionError" in error_msg or 
            "ServiceUnavailable" in error_msg or
            "refused" in error_msg.lower()):
            logger.warning(f"Neo4j connection issue for project {project_id}, returning empty graph")
            return {"nodes": [], "edges": []}
        
        # For other errors, still return empty graph to prevent UI breakage
        logger.warning(f"Graph fetch error for project {project_id}, returning empty graph: {error_msg}")
        return {"nodes": [], "edges": []}


@router.post("/api/projects/{project_id}/nodes")
async def create_node(project_id: str, node: NodeCreate, user_id: str = "default"):
    """Create a new node."""
    try:
        # Ensure id is set
        if "id" not in node.properties:
            node.properties["id"] = str(uuid.uuid4())
        
        created_node = GraphRepository.create_node(
            project_id=project_id,
            labels=node.labels,
            properties=node.properties
        )
        
        # Log command for undo
        inverse_payload = {"action": "delete", "node_id": created_node["id"]}
        CommandLog.log_command(
            project_id=project_id,
            user_id=user_id,
            command_type="create_node",
            payload={"action": "create", "node": created_node},
            inverse_payload=inverse_payload
        )
        
        return {"success": True, "node": created_node}
    except Exception as e:
        logger.error("Failed to create node", error=str(e), project_id=project_id)
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/api/projects/{project_id}/nodes/{node_id}")
async def update_node(project_id: str, node_id: str, node: NodeUpdate, user_id: str = "default"):
    """Update node properties."""
    try:
        # Get current state for undo
        # In production, fetch current node first
        updated_node = GraphRepository.update_node(node_id, node.properties)
        
        # Log command
        inverse_payload = {"action": "update", "node_id": node_id, "properties": {}}  # Would need old properties
        CommandLog.log_command(
            project_id=project_id,
            user_id=user_id,
            command_type="update_node",
            payload={"action": "update", "node": updated_node},
            inverse_payload=inverse_payload
        )
        
        return {"success": True, "node": updated_node}
    except Exception as e:
        logger.error("Failed to update node", error=str(e), node_id=node_id)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/api/projects/{project_id}/nodes/{node_id}")
async def delete_node(project_id: str, node_id: str, user_id: str = "default"):
    """Delete a node."""
    try:
        # Get node before deletion for undo
        # In production, fetch node first
        deleted = GraphRepository.delete_node(node_id)
        
        if deleted:
            # Log command
            inverse_payload = {"action": "create", "node": {}}  # Would need full node data
            CommandLog.log_command(
                project_id=project_id,
                user_id=user_id,
                command_type="delete_node",
                payload={"action": "delete", "node_id": node_id},
                inverse_payload=inverse_payload
            )
            return {"success": True}
        else:
            raise HTTPException(status_code=404, detail="Node not found")
    except Exception as e:
        logger.error("Failed to delete node", error=str(e), node_id=node_id)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/projects/{project_id}/relationships")
async def create_relationship(project_id: str, rel: RelationshipCreate, user_id: str = "default"):
    """Create a relationship."""
    try:
        created_rel = GraphRepository.create_relationship(
            source_id=rel.source_id,
            target_id=rel.target_id,
            rel_type=rel.rel_type,
            properties=rel.properties or {}
        )
        
        # Log command
        inverse_payload = {"action": "delete", "source_id": rel.source_id, "target_id": rel.target_id, "rel_type": rel.rel_type}
        CommandLog.log_command(
            project_id=project_id,
            user_id=user_id,
            command_type="create_relationship",
            payload={"action": "create", "relationship": created_rel},
            inverse_payload=inverse_payload
        )
        
        return {"success": True, "relationship": created_rel}
    except Exception as e:
        logger.error("Failed to create relationship", error=str(e), project_id=project_id)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/api/projects/{project_id}/relationships")
async def delete_relationship(
    project_id: str,
    source_id: str,
    target_id: str,
    rel_type: str,
    user_id: str = "default"
):
    """Delete a relationship."""
    try:
        deleted = GraphRepository.delete_relationship(source_id, target_id, rel_type)
        
        if deleted:
            # Log command
            inverse_payload = {"action": "create", "source_id": source_id, "target_id": target_id, "rel_type": rel_type}
            CommandLog.log_command(
                project_id=project_id,
                user_id=user_id,
                command_type="delete_relationship",
                payload={"action": "delete", "source_id": source_id, "target_id": target_id, "rel_type": rel_type},
                inverse_payload=inverse_payload
            )
            return {"success": True}
        else:
            raise HTTPException(status_code=404, detail="Relationship not found")
    except Exception as e:
        logger.error("Failed to delete relationship", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/projects/{project_id}/search")
async def search_nodes(
    project_id: str,
    q: str = Query(..., min_length=1),
    labels: Optional[str] = Query(None)
):
    """Search nodes."""
    try:
        label_list = labels.split(",") if labels else None
        results = GraphRepository.search(project_id, q, label_list)
        return {"success": True, "results": results}
    except Exception as e:
        logger.error("Failed to search", error=str(e), project_id=project_id)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/projects/{project_id}/validate")
async def validate_graph(project_id: str):
    """Validate graph consistency."""
    try:
        issues = GraphValidator.validate_project(project_id)
        return {"success": True, "issues": issues}
    except Exception as e:
        logger.error("Failed to validate graph", error=str(e), project_id=project_id)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/projects/{project_id}/render")
async def render_manuscript(project_id: str):
    """Render manuscript from graph."""
    try:
        result = GraphRenderer.render_manuscript(project_id)
        return {"success": True, **result}
    except Exception as e:
        logger.error("Failed to render manuscript", error=str(e), project_id=project_id)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/projects/{project_id}/commands")
async def get_commands(project_id: str, limit: int = Query(100, ge=1, le=1000)):
    """Get command history."""
    try:
        commands = CommandLog.get_commands(project_id, limit)
        return {"success": True, "commands": commands}
    except Exception as e:
        logger.error("Failed to get commands", error=str(e), project_id=project_id)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/projects/{project_id}/schema")
async def get_schema():
    """Get graph schema (labels, relationship types, allowed combinations)."""
    return {
        "success": True,
        "node_labels": NODE_LABELS,
        "relationship_types": RELATIONSHIP_TYPES,
        "allowed_relationships": ALLOWED_RELATIONSHIPS
    }


@router.get("/api/graph/status")
async def get_neo4j_status():
    """Check Neo4j connection status."""
    try:
        from app.graph.connection import get_neo4j_driver
        from app.core.config import settings
        
        status = {
            "neo4j_available": False,
            "neo4j_uri": settings.NEO4J_URI,
            "neo4j_user": settings.NEO4J_USER,
            "error": None,
            "message": None
        }
        
        try:
            driver = get_neo4j_driver()
            driver.verify_connectivity()
            status["neo4j_available"] = True
            status["message"] = "Neo4j is connected and running"
            logger.info("Neo4j status check: connected")
        except ConnectionError as e:
            status["neo4j_available"] = False
            status["error"] = str(e)
            status["message"] = "Neo4j is not running. Start it with: neo4j start or docker-compose up -d neo4j"
            logger.warning(f"Neo4j status check: not available - {e}")
        except Exception as e:
            status["neo4j_available"] = False
            status["error"] = str(e)
            status["message"] = f"Neo4j connection error: {str(e)}"
            logger.error(f"Neo4j status check failed: {e}")
        
        return status
    except Exception as e:
        logger.error(f"Failed to check Neo4j status: {e}")
        return {
            "neo4j_available": False,
            "error": str(e),
            "message": "Failed to check Neo4j status"
        }

