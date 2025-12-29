# Neo4j Knowledge Graph System

## Overview

This module provides a complete Neo4j-backed knowledge graph system for managing book canon (characters, locations, scenes, events, etc.) with a 3D interactive visualization interface.

## Architecture

### Backend Components

- **`connection.py`**: Neo4j driver connection management
- **`schema.py`**: Graph schema definitions, constraints, indexes, and validation rules
- **`repository.py`**: CRUD operations for nodes and relationships
- **`validation.py`**: Continuity and consistency checking
- **`renderer.py`**: Graph-to-manuscript rendering engine
- **`commands.py`**: Command log for undo/redo functionality

### Frontend Components

- **`writer/src/pages/graph-editor/index.tsx`**: 3D graph visualization and editing interface

## Setup

### 1. Start Neo4j

```bash
docker-compose up -d neo4j
```

Neo4j will be available at:
- HTTP: http://localhost:7474
- Bolt: bolt://localhost:7687

Default credentials:
- Username: `neo4j`
- Password: `neo4jpassword`

### 2. Initialize Schema

The schema is automatically initialized when the FastAPI app starts. You can also run manually:

```bash
python -m app.graph.schema
```

### 3. Install Frontend Dependencies

```bash
cd writer
npm install
npm run build
```

## API Endpoints

### Graph Operations

- `POST /api/projects/{project_id}/graph/init` - Initialize graph for a project
- `GET /api/projects/{project_id}/graph` - Fetch subgraph with filters
- `GET /api/projects/{project_id}/schema` - Get graph schema

### Node Operations

- `POST /api/projects/{project_id}/nodes` - Create node
- `PATCH /api/projects/{project_id}/nodes/{node_id}` - Update node
- `DELETE /api/projects/{project_id}/nodes/{node_id}` - Delete node

### Relationship Operations

- `POST /api/projects/{project_id}/relationships` - Create relationship
- `DELETE /api/projects/{project_id}/relationships` - Delete relationship

### Search & Validation

- `GET /api/projects/{project_id}/search` - Search nodes
- `POST /api/projects/{project_id}/validate` - Validate graph consistency
- `POST /api/projects/{project_id}/render` - Render manuscript from graph

### Command History

- `GET /api/projects/{project_id}/commands` - Get command history

## Graph Schema

### Node Labels

- `Project` - Root project node
- `Character` - Characters in the story
- `Location` - Physical locations
- `Environment` - Environmental settings
- `Faction` - Groups/organizations
- `Artifact` - Objects/items
- `Concept` - Abstract concepts
- `Rule` - World rules/laws
- `Theme` - Thematic elements
- `Chapter` - Book chapters
- `Scene` - Individual scenes
- `Event` - Plot events
- `Issue` - Validation issues
- `Source` - Reference sources

### Relationship Types

See `app/graph/schema.py` for complete list and allowed combinations.

## Usage

### Accessing the Graph Editor

1. Open a Book Publishing House project
2. Click the "🕸️ Knowledge Graph" button
3. The 3D graph editor will open

### Creating Nodes

1. Use the API or add UI controls to create nodes
2. Nodes are automatically connected to the Project node

### Creating Relationships

1. Click "Connect Mode" button
2. Click source node
3. Click target node
4. Enter relationship type
5. Relationship is created

### Validating Graph

Click "Validate" button to run continuity checks and see issues.

### Rendering Manuscript

Click "Render Book" to generate markdown manuscript from graph state.

## Integration with Book Publishing House

When a new project is created in Book Publishing House, a corresponding Neo4j Project node is automatically created. You can then:

1. Add characters, locations, scenes, etc. to the graph
2. Connect them with relationships
3. Validate consistency
4. Render the manuscript from the graph

## Performance Considerations

- Subgraph queries use depth limits to avoid loading entire graph
- Filters (labels, stage, chapter) reduce data size
- Large graphs (10k+ nodes) should use aggressive filtering
- Consider clustering/collapse for visualization of large graphs

## Security

- Neo4j credentials are never exposed to the browser
- All queries use parameterized Cypher (no injection risk)
- Relationship validation prevents invalid connections
- RBAC can be added per-project basis

## Future Enhancements

- Undo/redo UI implementation
- Advanced filtering UI
- Multiple view modes (timeline, character arcs, etc.)
- Layout persistence
- Collaborative editing
- Real-time updates via WebSocket

