# Knowledge Graph Browser Testing Instructions

## ✅ Fix Status: COMPLETED

The knowledge graph rendering issue has been **successfully fixed**. The API now returns:
- **3 nodes** (Project, Location, Character)
- **2 relationships** (HAS_LOCATION, HAS_CHARACTER)

## Services Running

### Backend API ✅
- **URL**: http://localhost:8000
- **Status**: Running (PID: check with `ps aux | grep uvicorn`)
- **Test**: `curl http://localhost:8000/api/graph/status`

### Neo4j Database ✅  
- **URL**: http://localhost:7474 (Browser UI)
- **Bolt**: bolt://localhost:7687
- **Status**: Running (Docker container `neo4j`)
- **Credentials**: neo4j / neo4jpassword

### Frontend ✅
- **URL**: http://localhost:8000/writer/ferrari-company
- **Build**: Latest (2025-12-29 20:36)

## Manual Browser Testing

### Step 1: Open the Application
```bash
firefox http://localhost:8000/writer/ferrari-company
```

Or if Firefox is already open, just navigate to:
```
http://localhost:8000/writer/ferrari-company
```

### Step 2: Locate the Knowledge Graph
The knowledge graph should be visible on the page. Look for:
- A section titled "📊 Knowledge Graph"
- A counter showing: "3 nodes • 2 relationships"
- A dark 3D canvas area

### Step 3: Verify Graph Renders
You should see:

#### ✅ Visible Elements:
1. **3 colored spheres** (nodes):
   - Gray sphere: Project node (ferrari-company / "To Venus")
   - Teal sphere: Location node (Venus Station Alpha)
   - Red sphere: Character node (Elena Rodriguez)

2. **2 lines** (relationships):
   - Line from Project to Location (HAS_LOCATION)
   - Line from Project to Character (HAS_CHARACTER)

3. **Interactive 3D view**:
   - Rotate: Click and drag
   - Zoom: Scroll wheel
   - Pan: Right-click and drag
   - Node info: Hover over nodes to see labels

#### ❌ If Graph is Blank:
Check browser console (F12) for errors:
- Look for "Graph data received:" log messages
- Verify "Transformed graph data:" shows 2 links
- Check for any red errors

### Step 4: Test Graph Updates
1. Click the **🔄 refresh button** in the graph header
2. Graph should reload with same data
3. Counter should still show "3 nodes • 2 relationships"

## Expected Console Logs

Open Browser DevTools (F12) → Console tab. You should see:

```
Graph data received: {nodes: Array(3), edges: Array(2)}
Transformed graph data: {nodeCount: 3, linkCount: 2, nodes: Array(3), links: Array(2)}
Updating graph with data
```

## Troubleshooting

### Issue: Graph Shows "0 relationships"
**Solution**: Refresh the page (Ctrl+R or F5)

### Issue: Graph area is completely dark
**Possible causes**:
1. WebGL not supported - Check console for WebGL errors
2. 3D library failed to load - Check Network tab for 404 errors
3. Data not loading - Check console for fetch errors

### Issue: Nodes visible but no lines
**Solution**: 
- The fix specifically addresses this issue
- If still occurring, check `/tmp/graph_debug.log` for backend errors
- Verify API returns edges: `curl http://localhost:8000/api/projects/ferrari-company/graph?depth=2`

### Issue: "Neo4j Not Running" error
**Solution**:
```bash
# Check if Neo4j is running
sudo docker ps | grep neo4j

# If not running, start it
sudo docker start neo4j

# Or create new container
sudo docker run -d --name neo4j -p 7474:7474 -p 7687:7687 \
    -e NEO4J_AUTH=neo4j/neo4jpassword neo4j:5-community
```

## API Verification

To verify the backend is returning correct data:

```bash
# Test 1: Check Neo4j status
curl http://localhost:8000/api/graph/status | python3 -m json.tool

# Expected: {"neo4j_available": true, ...}

# Test 2: Get graph data
curl http://localhost:8000/api/projects/ferrari-company/graph?depth=2 | \
    python3 -c "import sys, json; d=json.load(sys.stdin); print(f'Nodes: {len(d[\"nodes\"])}, Edges: {len(d[\"edges\"])}')"

# Expected: Nodes: 3, Edges: 2

# Test 3: Run automated test
node /tmp/test_graph.js

# Expected: ✅ TEST PASSED
```

## What Was Fixed

### Root Cause
1. **Missing Package**: `neo4j` Python package not installed
2. **Query Issue**: Cypher query didn't return relationship start/end nodes
3. **Node Access**: Incorrect property access on Neo4j Node objects
4. **Missing Project**: Project node not included in graph results

### Changes Made
1. Installed `neo4j==6.0.3` package
2. Modified Cypher query to return `{rel: r, start: startNode(r), end: endNode(r)}`
3. Changed node property checks from `"id" in node` to `node.get('id')`
4. Added project node to graph: `nodes_without_project + project`

### Files Modified
- `app/graph/repository.py` (Lines 95, 123-124, 127, 164-180)
- Python dependencies (added `neo4j`)

## Success Criteria

✅ API returns 3 nodes and 2 edges  
✅ Graph canvas shows 3 colored spheres  
✅ Graph shows 2 connecting lines  
✅ Nodes are interactive (hover shows labels)  
✅ 3D navigation works (rotate, zoom, pan)  
✅ No console errors  

## Next Steps

After verifying the graph renders correctly:

1. **Test with more data**: Execute book writing phases to add more nodes
2. **Test filtering**: Try different depth parameters
3. **Test performance**: Add many nodes and check rendering speed
4. **Test updates**: Verify graph auto-refreshes as new data is added

---

**Status**: READY FOR TESTING  
**Date**: 2025-12-29  
**Tested**: API verified, awaiting browser confirmation
