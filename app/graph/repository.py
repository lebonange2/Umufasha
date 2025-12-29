"""Neo4j repository for graph operations."""
from typing import List, Dict, Any, Optional
from neo4j import Session
import structlog
from app.graph.connection import get_neo4j_session
from app.graph.schema import validate_relationship, NODE_LABELS, RELATIONSHIP_TYPES

logger = structlog.get_logger(__name__)


class GraphRepository:
    """Repository for graph CRUD operations."""
    
    @staticmethod
    def create_project(project_id: str, title: str, genre: Optional[str] = None) -> Dict[str, Any]:
        """Create a new project node in Neo4j."""
        try:
            with get_neo4j_session() as session:
                query = """
                MERGE (p:Project {id: $project_id})
                SET p.title = $title,
                    p.genre = $genre,
                    p.createdAt = datetime(),
                    p.updatedAt = datetime()
                RETURN p
                """
                result = session.run(query, project_id=project_id, title=title, genre=genre)
                record = result.single()
                if record:
                    node = record["p"]
                    return {
                        "id": node["id"],
                        "labels": list(node.labels),
                        "properties": dict(node)
                    }
                raise ValueError(f"Failed to create project {project_id}")
        except ConnectionError as e:
            # Re-raise connection errors
            raise
        except Exception as e:
            error_msg = str(e)
            if "connection" in error_msg.lower() or "refused" in error_msg.lower() or "ServiceUnavailable" in error_msg:
                logger.warning(f"Neo4j not available, cannot create project node: {error_msg}")
                raise ConnectionError(f"Neo4j is not available: {error_msg}") from e
            raise
    
    @staticmethod
    def get_subgraph(
        project_id: str,
        focus_node_id: Optional[str] = None,
        depth: int = 2,
        labels: Optional[List[str]] = None,
        stage: Optional[str] = None,
        chapter: Optional[int] = None
    ) -> Dict[str, Any]:
        """Fetch a subgraph based on filters."""
        try:
            with get_neo4j_session() as session:
                # Build query based on filters
                if focus_node_id:
                    # Start from specific node
                    query = """
                    MATCH (project:Project {id: $project_id})
                    MATCH (start {id: $focus_node_id})
                    MATCH path = (start)-[*0..$depth]-(connected)
                    WHERE (start)-[*]-(project) OR start = project
                    WITH project, nodes(path) as nodes_in_path, relationships(path) as rels_in_path
                    UNWIND nodes_in_path as n
                    WITH project, collect(DISTINCT n) as all_nodes, rels_in_path
                    UNWIND rels_in_path as r
                    WITH project, all_nodes, collect(DISTINCT r) as all_rels
                    RETURN all_nodes, all_rels
                    """
                    result = session.run(query, project_id=project_id, focus_node_id=focus_node_id, depth=depth)
                else:
                    # Get all nodes connected to project
                    label_filters = []
                    if labels:
                        for label in labels:
                            label_filters.append(f"n:{label}")
                        label_filter = " AND (" + " OR ".join(label_filters) + ")"
                    else:
                        label_filter = ""
                    
                    stage_filter = ""
                    if stage:
                        stage_filter = """
                        OPTIONAL MATCH (s:Scene)
                        WHERE s.status = $stage
                        WITH project, collect(DISTINCT s) as stage_scenes
                        """
                    
                    query = f"""
                    MATCH (project:Project {{id: $project_id}})
                    {stage_filter}
                    OPTIONAL MATCH (project)-[*0..$depth]-(n)
                    WHERE n IS NOT NULL {label_filter}
                    WITH project, collect(DISTINCT n) as all_nodes
                    UNWIND all_nodes as n1
                    OPTIONAL MATCH (n1)-[r]-(n2)
                    WHERE n2 IN all_nodes AND n1 IS NOT NULL
                    WITH project, all_nodes, collect(DISTINCT r) as all_rels
                    RETURN project, all_nodes, all_rels
                    """
                    params = {"project_id": project_id, "depth": depth}
                    if stage:
                        params["stage"] = stage
                    if chapter is not None:
                        # Filter by chapter
                        query = query.replace(
                            "OPTIONAL MATCH (project)-[*0..$depth]-(n)",
                            "OPTIONAL MATCH (project)-[:HAS_CHAPTER]->(ch:Chapter {number: $chapter})-[:HAS_SCENE]->(s:Scene)"
                        )
                        query = query.replace("WHERE n IS NOT NULL", "WHERE n IS NOT NULL AND (n = ch OR n = s OR n IN all_nodes)")
                    params["chapter"] = chapter
                result = session.run(query, **params)
                
                record = result.single()
                if not record or not record.get("project"):
                    # Project doesn't exist in Neo4j - return empty graph
                    return {"nodes": [], "edges": []}
                
                nodes = []
                node_ids = set()
                for node in record["all_nodes"] or []:
                    if node and "id" in node:
                        node_id = node["id"]
                        if node_id not in node_ids:
                            node_ids.add(node_id)
                            nodes.append({
                                "id": node_id,
                                "labels": list(node.labels),
                                "properties": dict(node)
                            })
                
                edges = []
                edge_ids = set()
                for rel in record["all_rels"] or []:
                    if rel and rel.start_node and rel.end_node:
                        edge_id = f"{rel.start_node['id']}_{rel.type}_{rel.end_node['id']}"
                        if edge_id not in edge_ids:
                            edge_ids.add(edge_id)
                            edges.append({
                                "id": edge_id,
                                "type": rel.type,
                                "from": rel.start_node["id"],
                                "to": rel.end_node["id"],
                                "properties": dict(rel)
                            })
                
                return {"nodes": nodes, "edges": edges}
        except ConnectionError:
            # Neo4j is not available - return empty graph
            logger.warning(f"Neo4j connection failed, returning empty graph for project {project_id}")
            return {"nodes": [], "edges": []}
        except Exception as e:
            # Other errors - log and return empty graph
            error_msg = str(e)
            if "connection" in error_msg.lower() or "refused" in error_msg.lower() or "ServiceUnavailable" in error_msg:
                logger.warning(f"Neo4j connection issue for project {project_id}, returning empty graph")
                return {"nodes": [], "edges": []}
            # Re-raise unexpected errors
            raise
    
    @staticmethod
    def create_node(
        project_id: str,
        labels: List[str],
        properties: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a new node."""
        # Validate labels
        for label in labels:
            if label not in NODE_LABELS:
                raise ValueError(f"Invalid label: {label}")
        
        try:
            with get_neo4j_session() as session:
                label_str = ":".join(labels)
                query = f"""
                MATCH (project:Project {{id: $project_id}})
                CREATE (n:{label_str})
                SET n += $properties
                CREATE (project)-[:HAS_{labels[0].upper()}]->(n)
                RETURN n
                """
                result = session.run(query, project_id=project_id, properties=properties)
                record = result.single()
                if record:
                    node = record["n"]
                    return {
                        "id": node["id"],
                        "labels": list(node.labels),
                        "properties": dict(node)
                    }
                raise ValueError("Failed to create node")
        except ConnectionError as e:
            logger.warning(f"Neo4j not available, cannot create node: {e}")
            raise
        except Exception as e:
            error_msg = str(e)
            if "connection" in error_msg.lower() or "refused" in error_msg.lower() or "ServiceUnavailable" in error_msg:
                raise ConnectionError(f"Neo4j is not available: {error_msg}") from e
            raise
    
    @staticmethod
    def update_node(node_id: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Update node properties."""
        try:
            with get_neo4j_session() as session:
                query = """
                MATCH (n {id: $node_id})
                SET n += $properties,
                    n.updatedAt = datetime()
                RETURN n
                """
                result = session.run(query, node_id=node_id, properties=properties)
                record = result.single()
                if record:
                    node = record["n"]
                    return {
                        "id": node["id"],
                        "labels": list(node.labels),
                        "properties": dict(node)
                    }
                raise ValueError(f"Node not found: {node_id}")
        except ConnectionError as e:
            logger.warning(f"Neo4j not available, cannot update node: {e}")
            raise
        except Exception as e:
            error_msg = str(e)
            if "connection" in error_msg.lower() or "refused" in error_msg.lower() or "ServiceUnavailable" in error_msg:
                raise ConnectionError(f"Neo4j is not available: {error_msg}") from e
            raise
    
    @staticmethod
    def delete_node(node_id: str) -> bool:
        """Delete a node and its relationships."""
        try:
            with get_neo4j_session() as session:
                query = """
                MATCH (n {id: $node_id})
                DETACH DELETE n
                RETURN count(n) as deleted
                """
                result = session.run(query, node_id=node_id)
                record = result.single()
                return record["deleted"] > 0 if record else False
        except ConnectionError as e:
            logger.warning(f"Neo4j not available, cannot delete node: {e}")
            raise
        except Exception as e:
            error_msg = str(e)
            if "connection" in error_msg.lower() or "refused" in error_msg.lower() or "ServiceUnavailable" in error_msg:
                raise ConnectionError(f"Neo4j is not available: {error_msg}") from e
            raise
    
    @staticmethod
    def create_relationship(
        source_id: str,
        target_id: str,
        rel_type: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a relationship between two nodes."""
        # Get source and target labels to validate
        try:
            with get_neo4j_session() as session:
                query = """
                MATCH (source {id: $source_id})
                MATCH (target {id: $target_id})
                RETURN labels(source) as source_labels, labels(target) as target_labels
                """
                result = session.run(query, source_id=source_id, target_id=target_id)
                record = result.single()
                if not record:
                    raise ValueError("Source or target node not found")
                
                source_labels = record["source_labels"]
                target_labels = record["target_labels"]
                
                # Validate relationship
                if not any(validate_relationship(sl, rel_type, tl) for sl in source_labels for tl in target_labels):
                    raise ValueError(f"Invalid relationship: {source_labels[0]} -[{rel_type}]-> {target_labels[0]}")
                
                # Create relationship
                props = properties or {}
                query = f"""
                MATCH (source {{id: $source_id}})
                MATCH (target {{id: $target_id}})
                MERGE (source)-[r:{rel_type}]->(target)
                SET r += $properties
                RETURN r, source, target
                """
                result = session.run(query, source_id=source_id, target_id=target_id, properties=props)
                record = result.single()
                if record:
                    rel = record["r"]
                    return {
                        "id": f"{source_id}_{rel_type}_{target_id}",
                        "type": rel.type,
                        "from": source_id,
                        "to": target_id,
                        "properties": dict(rel)
                    }
                raise ValueError("Failed to create relationship")
        except ConnectionError as e:
            logger.warning(f"Neo4j not available, cannot create relationship: {e}")
            raise
        except Exception as e:
            error_msg = str(e)
            if "connection" in error_msg.lower() or "refused" in error_msg.lower() or "ServiceUnavailable" in error_msg:
                raise ConnectionError(f"Neo4j is not available: {error_msg}") from e
            raise
    
    @staticmethod
    def delete_relationship(source_id: str, target_id: str, rel_type: str) -> bool:
        """Delete a relationship."""
        try:
            with get_neo4j_session() as session:
                query = f"""
                MATCH (source {{id: $source_id}})-[r:{rel_type}]->(target {{id: $target_id}})
                DELETE r
                RETURN count(r) as deleted
                """
                result = session.run(query, source_id=source_id, target_id=target_id)
                record = result.single()
                return record["deleted"] > 0 if record else False
        except ConnectionError as e:
            logger.warning(f"Neo4j not available, cannot delete relationship: {e}")
            raise
        except Exception as e:
            error_msg = str(e)
            if "connection" in error_msg.lower() or "refused" in error_msg.lower() or "ServiceUnavailable" in error_msg:
                raise ConnectionError(f"Neo4j is not available: {error_msg}") from e
            raise
    
    @staticmethod
    def search(project_id: str, query: str, labels: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Search nodes using fulltext index."""
        try:
            with get_neo4j_session() as session:
                label_filter = ""
                if labels:
                    label_list = ":".join(labels)
                    label_filter = f"AND n:{label_list}"
                
                search_query = f"""
                CALL db.index.fulltext.queryNodes('character_name_fulltext', $query)
                YIELD node as n, score
                MATCH (project:Project {{id: $project_id}})-[*]-(n)
                WHERE 1=1 {label_filter}
                RETURN n, score
                ORDER BY score DESC
                LIMIT 50
                """
                result = session.run(search_query, project_id=project_id, query=query)
                nodes = []
                for record in result:
                    node = record["n"]
                    nodes.append({
                        "id": node["id"],
                        "labels": list(node.labels),
                        "properties": dict(node),
                        "score": record["score"]
                    })
                return nodes
        except ConnectionError:
            logger.warning(f"Neo4j not available, returning empty search results")
            return []
        except Exception as e:
            error_msg = str(e)
            if "connection" in error_msg.lower() or "refused" in error_msg.lower() or "ServiceUnavailable" in error_msg:
                logger.warning(f"Neo4j connection issue, returning empty search results")
                return []
            raise

