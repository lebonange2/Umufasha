"""In-memory graph storage to replace Neo4j when unavailable."""
from typing import List, Dict, Any, Optional
from collections import defaultdict
import structlog
import json
from pathlib import Path
import threading

logger = structlog.get_logger(__name__)


class MemoryGraphStore:
    """Simple in-memory graph database that can replace Neo4j."""
    
    def __init__(self, persist_path: Optional[str] = None):
        """Initialize the memory store.
        
        Args:
            persist_path: Optional path to persist data to JSON file
        """
        self._nodes: Dict[str, Dict[str, Any]] = {}  # node_id -> {labels, properties}
        self._relationships: List[Dict[str, Any]] = []  # List of relationships
        self._project_nodes: Dict[str, str] = {}  # project_id -> node_id
        self._lock = threading.RLock()
        self._persist_path = persist_path
        
        # Load persisted data if available
        if persist_path:
            self._load_from_file()
    
    def _load_from_file(self):
        """Load graph data from JSON file."""
        if not self._persist_path:
            return
        
        path = Path(self._persist_path)
        if not path.exists():
            return
        
        try:
            with open(path, 'r') as f:
                data = json.load(f)
                self._nodes = {k: v for k, v in data.get('nodes', {}).items()}
                self._relationships = data.get('relationships', [])
                self._project_nodes = data.get('project_nodes', {})
            logger.info(f"Loaded graph data from {self._persist_path}")
        except Exception as e:
            logger.warning(f"Failed to load graph data from {self._persist_path}: {e}")
    
    def _save_to_file(self):
        """Save graph data to JSON file."""
        if not self._persist_path:
            return
        
        try:
            path = Path(self._persist_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, 'w') as f:
                json.dump({
                    'nodes': self._nodes,
                    'relationships': self._relationships,
                    'project_nodes': self._project_nodes
                }, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save graph data to {self._persist_path}: {e}")
    
    def create_project(self, project_id: str, title: str, genre: Optional[str] = None) -> Dict[str, Any]:
        """Create a new project node."""
        with self._lock:
            node_id = f"project_{project_id}"
            if node_id in self._nodes:
                # Project already exists, return it
                node = self._nodes[node_id]
                return {
                    "id": node_id,
                    "labels": node.get("labels", ["Project"]),
                    "properties": node.get("properties", {})
                }
            
            node = {
                "labels": ["Project"],
                "properties": {
                    "id": project_id,
                    "title": title,
                    "genre": genre or "",
                    "createdAt": None,  # Could add datetime if needed
                    "updatedAt": None
                }
            }
            self._nodes[node_id] = node
            self._project_nodes[project_id] = node_id
            self._save_to_file()
            
            return {
                "id": node_id,
                "labels": node["labels"],
                "properties": node["properties"]
            }
    
    def get_subgraph(
        self,
        project_id: str,
        focus_node_id: Optional[str] = None,
        depth: int = 2,
        labels: Optional[List[str]] = None,
        stage: Optional[str] = None,
        chapter: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get subgraph for a project."""
        with self._lock:
            project_node_id = self._project_nodes.get(project_id)
            if not project_node_id or project_node_id not in self._nodes:
                return {"nodes": [], "edges": []}
            
            # Start from project node or focus node
            start_node_id = focus_node_id if focus_node_id else project_node_id
            
            # Collect nodes and relationships
            visited_nodes = set()
            nodes_to_process = [(start_node_id, 0)]  # (node_id, current_depth)
            result_nodes = []
            result_edges = []
            
            while nodes_to_process:
                current_node_id, current_depth = nodes_to_process.pop(0)
                
                if current_node_id in visited_nodes or current_depth > depth:
                    continue
                
                visited_nodes.add(current_node_id)
                
                if current_node_id in self._nodes:
                    node = self._nodes[current_node_id]
                    # Apply label filter if specified
                    if labels:
                        node_labels = node.get("labels", [])
                        if not any(label in node_labels for label in labels):
                            continue
                    
                    result_nodes.append({
                        "id": current_node_id,
                        "labels": node.get("labels", []),
                        "properties": node.get("properties", {})
                    })
                    
                    # Find relationships from this node
                    if current_depth < depth:
                        for rel in self._relationships:
                            if rel.get("from") == current_node_id:
                                target_id = rel.get("to")
                                if target_id not in visited_nodes:
                                    nodes_to_process.append((target_id, current_depth + 1))
                                result_edges.append({
                                    "id": rel.get("id", f"{rel['from']}_{rel['type']}_{rel['to']}"),
                                    "type": rel.get("type", ""),
                                    "from": rel["from"],
                                    "to": rel["to"],
                                    "properties": rel.get("properties", {})
                                })
                            elif rel.get("to") == current_node_id:
                                source_id = rel.get("from")
                                if source_id not in visited_nodes:
                                    nodes_to_process.append((source_id, current_depth + 1))
                                result_edges.append({
                                    "id": rel.get("id", f"{rel['from']}_{rel['type']}_{rel['to']}"),
                                    "type": rel.get("type", ""),
                                    "from": rel["from"],
                                    "to": rel["to"],
                                    "properties": rel.get("properties", {})
                                })
            
            return {"nodes": result_nodes, "edges": result_edges}
    
    def create_node(
        self,
        project_id: str,
        labels: List[str],
        properties: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a new node."""
        with self._lock:
            # Generate node ID if not provided
            node_id = properties.get("id")
            if not node_id:
                node_id = f"{labels[0].lower()}_{len(self._nodes)}"
                properties["id"] = node_id
            
            node = {
                "labels": labels,
                "properties": properties
            }
            self._nodes[node_id] = node
            self._save_to_file()
            
            return {
                "id": node_id,
                "labels": labels,
                "properties": properties
            }
    
    def update_node(self, node_id: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Update node properties."""
        with self._lock:
            if node_id not in self._nodes:
                raise ValueError(f"Node not found: {node_id}")
            
            node = self._nodes[node_id]
            node["properties"].update(properties)
            self._save_to_file()
            
            return {
                "id": node_id,
                "labels": node.get("labels", []),
                "properties": node["properties"]
            }
    
    def delete_node(self, node_id: str) -> bool:
        """Delete a node and its relationships."""
        with self._lock:
            if node_id not in self._nodes:
                return False
            
            # Remove relationships
            self._relationships = [
                rel for rel in self._relationships
                if rel.get("from") != node_id and rel.get("to") != node_id
            ]
            
            # Remove node
            del self._nodes[node_id]
            self._save_to_file()
            return True
    
    def create_relationship(
        self,
        source_id: str,
        target_id: str,
        rel_type: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a relationship between two nodes."""
        with self._lock:
            if source_id not in self._nodes or target_id not in self._nodes:
                raise ValueError("Source or target node not found")
            
            rel_id = f"{source_id}_{rel_type}_{target_id}"
            
            # Check if relationship already exists
            for rel in self._relationships:
                if rel.get("from") == source_id and rel.get("to") == target_id and rel.get("type") == rel_type:
                    # Update existing relationship
                    rel["properties"].update(properties or {})
                    self._save_to_file()
                    return {
                        "id": rel_id,
                        "type": rel_type,
                        "from": source_id,
                        "to": target_id,
                        "properties": rel["properties"]
                    }
            
            # Create new relationship
            rel = {
                "id": rel_id,
                "type": rel_type,
                "from": source_id,
                "to": target_id,
                "properties": properties or {}
            }
            self._relationships.append(rel)
            self._save_to_file()
            
            return rel
    
    def delete_relationship(self, source_id: str, target_id: str, rel_type: str) -> bool:
        """Delete a relationship."""
        with self._lock:
            initial_count = len(self._relationships)
            self._relationships = [
                rel for rel in self._relationships
                if not (rel.get("from") == source_id and rel.get("to") == target_id and rel.get("type") == rel_type)
            ]
            deleted = len(self._relationships) < initial_count
            if deleted:
                self._save_to_file()
            return deleted
    
    def search(self, project_id: str, query: str, labels: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Search nodes using text matching."""
        with self._lock:
            project_node_id = self._project_nodes.get(project_id)
            if not project_node_id:
                return []
            
            query_lower = query.lower()
            results = []
            
            for node_id, node in self._nodes.items():
                # Apply label filter
                if labels:
                    node_labels = node.get("labels", [])
                    if not any(label in node_labels for label in labels):
                        continue
                
                # Search in properties
                properties = node.get("properties", {})
                for key, value in properties.items():
                    if isinstance(value, str) and query_lower in value.lower():
                        results.append({
                            "id": node_id,
                            "labels": node.get("labels", []),
                            "properties": properties,
                            "score": 1.0  # Simple scoring
                        })
                        break
            
            return results[:50]  # Limit results


# Global instance
_memory_store: Optional[MemoryGraphStore] = None
_memory_store_lock = threading.Lock()


def get_memory_store(persist_path: Optional[str] = None) -> MemoryGraphStore:
    """Get or create the global memory store instance."""
    global _memory_store
    
    if _memory_store is None:
        with _memory_store_lock:
            if _memory_store is None:
                # Default persist path in project directory
                if persist_path is None:
                    persist_path = "graph_data/memory_graph.json"
                _memory_store = MemoryGraphStore(persist_path=persist_path)
    
    return _memory_store

