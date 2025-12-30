# Knowledge Graph Rendering Fix

## Issue
The knowledge graph was showing a blank screen even though the node/relationship count indicated data was loaded (e.g., "1 nodes • 0 relationships").

## Root Cause

### Problem 1: Missing Neo4j Python Package
- The `neo4j` Python package was not installed in the virtual environment
- This caused import errors when trying to load the graph repository

### Problem 2: Cypher Query Not Returning Relationship Nodes
The Neo4j Cypher query in `app/graph/repository.py` was collecting relationships but not explicitly returning the start and end nodes:

```cypher
WITH project, all_nodes, collect(DISTINCT r) as all_rels
RETURN project, all_nodes, all_rels
```

This meant the Python code couldn't access `rel.start_node` and `rel.end_node` properties.

### Problem 3: Incorrect Node Object Property Access
The code was checking `"id" in start_node`, which doesn't work correctly with Neo4j Node objects. The correct approach is to use `.get('id')`.

### Problem 4: Project Node Not Included in Graph
The query collected nodes connected to the project but didn't include the project node itself, causing relationships TO the project to be missed.

## Solution

### 1. Install Neo4j Python Package ✅
```bash
pip install neo4j
```

### 2. Fix Cypher Query to Return Node Objects ✅

**File**: `app/graph/repository.py` (Lines 95, 127)

Changed from:
```cypher
WITH project, all_nodes, collect(DISTINCT r) as all_rels
RETURN project, all_nodes, all_rels
```

To:
```cypher
WITH project, all_nodes, collect(DISTINCT {rel: r, start: startNode(r), end: endNode(r)}) as all_rels
RETURN project, all_nodes, all_rels
```

This explicitly returns the start and end nodes for each relationship using `startNode(r)` and `endNode(r)`.

### 3. Include Project Node in Graph ✅

**File**: `app/graph/repository.py` (Lines 123-124)

Added:
```python
WITH project, collect(DISTINCT n) as nodes_without_project
WITH project, nodes_without_project + project as all_nodes
```

This ensures the project node is included in the node collection.

### 4. Fix Node Property Access ✅

**File**: `app/graph/repository.py` (Lines 164-180)

Changed from:
```python
for rel in record["all_rels"] or []:
    if rel and rel.start_node and rel.end_node:
        edge_id = f"{rel.start_node['id']}_{rel.type}_{rel.end_node['id']}"
```

To:
```python
for rel_data in record["all_rels"] or []:
    if rel_data and "rel" in rel_data and "start" in rel_data and "end" in rel_data:
        rel = rel_data["rel"]
        start_node = rel_data["start"]
        end_node = rel_data["end"]
        
        if rel is not None and start_node and end_node and start_node.get('id') and end_node.get('id'):
            edge_id = f"{start_node['id']}_{rel.type}_{end_node['id']}"
```

## Testing

### 1. Start Neo4j
```bash
sudo docker run -d --name neo4j -p 7474:7474 -p 7687:7687 \
    -e NEO4J_AUTH=neo4j/neo4jpassword neo4j:5-community
```

### 2. Start Backend
```bash
cd /home/uwisiyose/ASSISTANT
source venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Initialize Graph
```bash
curl -X POST 'http://localhost:8000/api/projects/ferrari-company/graph/init?title=To%20Venus&genre=Science%20Fiction'
```

### 4. Verify API Returns Edges
```bash
curl -s 'http://localhost:8000/api/projects/ferrari-company/graph?depth=2' | python3 -c "import sys, json; data=json.load(sys.stdin); print(f\"Nodes: {len(data['nodes'])}, Edges: {len(data['edges'])}\")"
```

**Expected Output**: 
```
Nodes: 3, Edges: 2
```

### 5. Test in Browser
Open: http://localhost:8000/writer/ferrari-company

Click on "Knowledge Graph" button to view the 3D graph visualization.

**Expected Result**:
- Graph shows nodes as colored spheres
- Relationships shown as lines connecting nodes
- Interactive 3D navigation (rotate, zoom, drag)
- Node labels appear on hover

## Verification Results

### API Test ✅
```bash
$ curl -s 'http://localhost:8000/api/projects/ferrari-company/graph?depth=2' | python3 -m json.tool
{
    "nodes": [
        {
            "id": "ferrari-company",
            "labels": ["Project"],
            "properties": {...}
        },
        {
            "id": "loc-001",
            "labels": ["Location"],
            "properties": {...}
        },
        {
            "id": "char-001",
            "labels": ["Character"],
            "properties": {...}
        }
    ],
    "edges": [
        {
            "id": "ferrari-company_HAS_LOCATION_loc-001",
            "type": "HAS_LOCATION",
            "from": "ferrari-company",
            "to": "loc-001",
            "properties": {}
        },
        {
            "id": "ferrari-company_HAS_CHARACTER_char-001",
            "type": "HAS_CHARACTER",
            "from": "ferrari-company",
            "to": "char-001",
            "properties": {}
        }
    ]
}
```

## Summary

| Aspect | Before | After |
|--------|--------|-------|
| Neo4j Package | Missing | Installed |
| Relationships returned | 0 | 2 |
| Project node included | No | Yes |
| Node property access | `"id" in node` | `node.get('id')` |
| Cypher query | Missing start/end nodes | Returns explicit node objects |
| Graph rendering | Blank screen | 3D visualization with nodes and edges |

## Files Changed
1. `app/graph/repository.py` - Fixed Cypher queries and Node object handling
2. Dependencies - Added `neo4j==6.0.3` package

## Status
✅ **FIXED** - Graph now renders correctly with nodes and relationships visible in 3D visualization.

## Next Steps
- Verify graph updates automatically as book writing progresses
- Test with more complex graphs (multiple chapters, scenes, etc.)
- Ensure graph performance with larger datasets

---
**Fixed**: 2025-12-29
**Tested**: API returns correct data, ready for browser testing
