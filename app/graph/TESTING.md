# Testing Guide for Neo4j Knowledge Graph

## Setup for Testing

1. Start Neo4j:
```bash
docker-compose up -d neo4j
```

2. Wait for Neo4j to be ready (check health):
```bash
docker-compose ps neo4j
```

3. Initialize schema:
```bash
python scripts/init_neo4j_schema.py
```

## Manual Testing

### 1. Create a Project Graph

```bash
curl -X POST "http://localhost:8000/api/projects/test-project-123/graph/init?title=Test%20Book&genre=sci-fi"
```

### 2. Create a Character Node

```bash
curl -X POST "http://localhost:8000/api/projects/test-project-123/nodes" \
  -H "Content-Type: application/json" \
  -d '{
    "labels": ["Character"],
    "properties": {
      "id": "char_1",
      "name": "John Doe",
      "aliases": ["JD"],
      "traits": ["brave", "curious"]
    }
  }'
```

### 3. Create a Location Node

```bash
curl -X POST "http://localhost:8000/api/projects/test-project-123/nodes" \
  -H "Content-Type: application/json" \
  -d '{
    "labels": ["Location"],
    "properties": {
      "id": "loc_1",
      "name": "Mars Colony",
      "type": "settlement",
      "description": "A thriving colony on Mars"
    }
  }'
```

### 4. Create a Relationship

```bash
curl -X POST "http://localhost:8000/api/projects/test-project-123/relationships" \
  -H "Content-Type: application/json" \
  -d '{
    "source_id": "char_1",
    "target_id": "loc_1",
    "rel_type": "APPEARS_IN"
  }'
```

### 5. Fetch Subgraph

```bash
curl "http://localhost:8000/api/projects/test-project-123/graph"
```

### 6. Validate Graph

```bash
curl -X POST "http://localhost:8000/api/projects/test-project-123/validate"
```

### 7. Render Manuscript

```bash
curl -X POST "http://localhost:8000/api/projects/test-project-123/render"
```

## Frontend Testing

1. Start the application:
```bash
uvicorn app.main:app --reload
```

2. Build frontend:
```bash
cd writer && npm install && npm run build
```

3. Navigate to a Book Publishing House project
4. Click "🕸️ Knowledge Graph" button
5. Test interactions:
   - Click nodes to inspect
   - Drag nodes to reposition
   - Use "Connect Mode" to create relationships
   - Create new nodes
   - Validate graph
   - Render manuscript

## Integration Testing

The graph automatically syncs when:
- A new Book Publishing House project is created
- Phases complete (characters, locations, scenes are synced)

Check sync by:
1. Creating a project in Book Publishing House
2. Opening the graph editor
3. Verifying project node exists
4. After phases complete, checking if characters/locations/scenes appear

