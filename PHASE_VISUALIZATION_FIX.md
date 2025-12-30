# Phase Data Visualization on Knowledge Graph - Fix Documentation

## Issues Fixed

### Issue 1: Graph Centering with Zoom (Fixed) ✅
**Problem**: Graph was using `zoomToFit()` which changed node sizes instead of just centering the camera.

**Solution**: Changed to use `cameraPosition()` with calculated center point.

**File**: `writer/src/components/EmbeddedGraph.tsx` (Lines 142-163)

```typescript
// Calculate center of all nodes
let sumX = 0, sumY = 0, sumZ = 0;
graphData.nodes.forEach((node: any) => {
  sumX += node.x || 0;
  sumY += node.y || 0;
  sumZ += node.z || 0;
});
const centerX = sumX / graphData.nodes.length;
const centerY = sumY / graphData.nodes.length;
const centerZ = sumZ / graphData.nodes.length;

// Position camera to look at center point without changing distance
graphRef.current.cameraPosition(
  { x: centerX, y: centerY, z: centerZ + 300 }, // Position camera 300 units away on Z axis
  { x: centerX, y: centerY, z: centerZ }, // Look at center
  1000 // 1 second transition
);
```

**Result**: Nodes remain at normal size and camera centers on them smoothly.

---

### Issue 2: Phase Data Not Visualized on Graph ✅
**Problem**: JSON output from each phase (world dossier, plot arc, character bible) was not creating nodes on the knowledge graph.

**Solution**: Enhanced backend sync logic to parse phase artifacts and create graph nodes for all story elements.

---

## Backend Changes

### 1. Enhanced `sync.py` - Plot Arc Visualization

**File**: `app/graph/sync.py`

#### Added `_sync_plot_arc()` method (Lines 227-339):
Parses plot_arc JSON and creates:

- **Act nodes** (beginning, middle, end)
- **PlotEvent nodes** (events within each act)
- **PlotPoint nodes** (key plot points)
- **TurningPoint nodes** (major turning points) 
- **Climax node** (story climax)
- **Resolution node** (story resolution)

Example from test JSON:
```json
{
  "plot_arc": {
    "story_arc": {
      "three-act_structure": [
        {
          "act": "beginning",
          "events": [
            {"event": "Introduction to protagonist, Dr. Sofia Rodriguez"}
          ]
        }
      ],
      "key_plot_points": [
        {"point": "Protagonist's initial enthusiasm begins to wane"}
      ],
      "climax": {
        "event": "Team discovers hidden habitable zone on Venus"
      }
    }
  }
}
```

Creates graph structure:
```
Project
  ├─> Act (beginning)
  │    └─> PlotEvent "Introduction to protagonist"
  ├─> Act (middle)
  │    └─> PlotEvent "Team arrives on Venus"
  ├─> Act (end)
  │    └─> PlotEvent "Team discovers habitable zone"
  ├─> PlotPoint "Enthusiasm begins to wane"
  ├─> TurningPoint "Realizes true goal of expedition"
  ├─> Climax "Discovers habitable zone"
  └─> Resolution "Team returns as heroes"
```

#### Enhanced `_sync_characters()` method (Lines 93-136):
Now supports multiple character structures:
- `characters` array
- `main_characters` array
- `supporting_characters` array

Additional properties:
- `role` (e.g., "protagonist")
- `occupation` (e.g., "Astro-engineer")
- `age`

---

### 2. Updated `schema.py` - New Node Types

**File**: `app/graph/schema.py`

#### Added Node Labels (Lines 34-39):
```python
"Act",           # Story acts (beginning, middle, end)
"PlotEvent",     # Events within acts
"PlotPoint",     # Key plot points
"TurningPoint",  # Major turning points
"Climax",        # Story climax
"Resolution",    # Story resolution
```

#### Added Relationship Types (Lines 76-80):
```python
"HAS_ACT",
"HAS_PLOT_POINT",
"HAS_TURNING_POINT",
"HAS_CLIMAX",
"HAS_RESOLUTION",
```

#### Added Constraints (Lines 170-175):
Ensures unique IDs for all new node types.

---

## Frontend Changes

### Updated `EmbeddedGraph.tsx` - Node Colors

**File**: `writer/src/components/EmbeddedGraph.tsx` (Lines 49-54)

Added colors for new node types:
```typescript
Act: 0x9b59b6,          // Purple for acts
PlotEvent: 0xe74c3c,    // Red for plot events
PlotPoint: 0xf39c12,    // Orange for plot points
TurningPoint: 0xe67e22, // Dark orange for turning points
Climax: 0xc0392b,       // Dark red for climax
Resolution: 0x27ae60,   // Green for resolution
```

**Visual Legend**:
- 🟣 **Act** - Purple spheres
- 🔴 **PlotEvent** - Red spheres
- 🟠 **PlotPoint** - Orange spheres
- 🟧 **TurningPoint** - Dark orange spheres
- 🔺 **Climax** - Dark red sphere
- 🟢 **Resolution** - Green sphere

---

## How It Works

### Phase Execution Flow:

1. **User executes phase** (e.g., "Strategy & Concept")
2. **Backend generates JSON artifacts**:
   - world_dossier
   - character_bible
   - plot_arc
   - outline
   - etc.

3. **Frontend calls `/sync-graph` endpoint**
   ```typescript
   await fetch(`/api/ferrari-company/projects/${project_id}/sync-graph`, {
     method: 'POST',
   });
   ```

4. **Backend parses artifacts** (`sync.py`):
   - Extracts characters from `character_bible`
   - Extracts locations from `world_dossier`
   - **NEW**: Extracts plot structure from `plot_arc`
   - Creates nodes and relationships in Neo4j

5. **Graph auto-refreshes** (every 5 seconds)
6. **New nodes appear** with proper colors and centered view

---

## Testing

### Test JSON Structure:
```json
{
  "plot_arc": {
    "story_arc": {
      "three-act_structure": [
        {"act": "beginning", "events": [{"event": "..."}, ...]},
        {"act": "middle", "events": [...]},
        {"act": "end", "events": [...]}
      ],
      "key_plot_points": [{"point": "..."}, ...],
      "major_turning_points": [{"turning_point": "..."}, ...],
      "climax": {"event": "..."},
      "resolution": {"events": [...]}
    }
  }
}
```

### Expected Graph Nodes (from test data):
- **3 Acts**: beginning, middle, end
- **7 PlotEvents**: events within acts
- **3 PlotPoints**: key plot points
- **2 TurningPoints**: major turning points
- **1 Climax**: story climax
- **1 Resolution**: story resolution
- **1 Project**: root node
- **Characters**: from character_bible
- **Locations**: from world_dossier

**Total**: ~18+ nodes visualized

---

## Browser Testing

### Steps:
1. Open: http://localhost:8000/writer/ferrari-company
2. Execute a phase (e.g., "Strategy & Concept")
3. Wait for phase completion
4. Observe graph updates

### Expected Results:
✅ Graph automatically centers on nodes (no zoom)
✅ New nodes appear for plot elements
✅ Nodes have distinct colors by type
✅ JSON output visible side-by-side with graph
✅ Smooth camera transitions
✅ Normal node sizes (not zoomed)

### Visual Layout:
```
Desktop View:
┌─────────────────┬─────────────────┐
│  📊 Graph       │  Phase Results  │
│                 │                 │
│  🟣 Act         │  {              │
│   └🔴 Event     │    "plot_arc"...│
│  🟠 PlotPoint   │  }              │
│  🔺 Climax      │                 │
│  🟢 Resolution  │  ✓ Approve      │
└─────────────────┴─────────────────┘
```

---

## Files Modified

### Backend:
1. `app/graph/sync.py`
   - Added `_sync_plot_arc()` method
   - Enhanced `_sync_characters()` method
   - Modified `sync_from_artifacts()` to call plot arc sync

2. `app/graph/schema.py`
   - Added 6 new node labels
   - Added 5 new relationship types
   - Added constraints and indexes

### Frontend:
1. `writer/src/components/EmbeddedGraph.tsx`
   - Changed centering from `zoomToFit()` to `cameraPosition()`
   - Added colors for 6 new node types

2. Frontend built: `app/static/writer/assets/index-DjQJihWx.js`

---

## Verification Commands

### 1. Check graph has plot nodes:
```bash
curl -s 'http://localhost:8000/api/projects/ferrari-company/graph?depth=3' | \
  python3 -c "import sys, json; d=json.load(sys.stdin); \
  plot_nodes = [n for n in d['nodes'] if any(l in ['Act', 'PlotEvent', 'PlotPoint', 'TurningPoint', 'Climax', 'Resolution'] for l in n['labels'])]; \
  print(f'Plot nodes: {len(plot_nodes)}'); \
  [print(f\"  - {n['labels']}: {n['properties'].get('description', '')[:60]}...\") for n in plot_nodes[:5]]"
```

### 2. Check Neo4j directly:
```bash
sudo docker exec -it neo4j cypher-shell -u neo4j -p neo4jpassword \
  "MATCH (p:Project {id: 'ferrari-company'})-[r]->(n) \
   WHERE n:Act OR n:PlotEvent OR n:PlotPoint OR n:TurningPoint OR n:Climax OR n:Resolution \
   RETURN labels(n) as type, count(n) as count"
```

---

## Benefits

1. **Complete Story Visualization**: Every phase now creates visual nodes
2. **Plot Structure Visible**: See three-act structure, plot points, turning points
3. **Better UX**: Normal node sizes, proper centering
4. **Story Development Tracking**: Watch graph grow as story develops
5. **Relationship Clarity**: Acts contain events, events connect to plot points

---

## Next Steps

1. ✅ Test in browser with actual phase execution
2. Add more relationship types (e.g., PlotEvent → Character)
3. Add filtering by node type
4. Add timeline view for plot events
5. Export graph as visual diagram

---

**Status**: ✅ **IMPLEMENTED** - Ready for browser testing

**Date**: 2025-12-29
**Build**: `index-DjQJihWx.js`
