# Mindmapper - Visual Mind Mapping Tool

A fully-featured mind mapping application integrated into the Brainstorming section of the AI Assistant. Create, edit, save, load, and export visual mind maps with an intuitive interface.

## Features

### Core Functionality
- **Infinite Canvas**: Pan and zoom to navigate large mind maps
- **Node Management**: Create, edit, delete, and style nodes
- **Connections**: Automatic parent-child connections with visual edges
- **Styling**: Customize node colors, text colors, and shapes (rectangle/pill)
- **Auto-save**: Automatic saving with debouncing (2 seconds after changes)
- **Export**: Export mind maps as JSON, SVG, or PNG

### User Interface
- **Toolbar**: Title editing, save status, export options
- **Sidebar**: List of all mind maps with quick access
- **Canvas**: Interactive drawing area with pan/zoom controls
- **Inspector**: Property panel for selected nodes

### Keyboard Shortcuts
- `Tab`: Create child node from selected node
- `Enter`: Create sibling node
- `Delete` / `Backspace`: Delete selected node
- `Double-click`: Edit node text
- `Mouse wheel`: Zoom in/out
- `Click + drag`: Pan canvas

## Installation

### Prerequisites
- Python 3.8+
- Node.js 18+ and npm
- FastAPI backend running

### Backend Setup

1. **Database Migration**: The mindmap models are already added to `app/models.py`. Run the application to create the tables:
   ```bash
   python -m app.main
   ```
   Or if using a migration tool, create and run migrations.

2. **Dependencies**: Ensure all FastAPI dependencies are installed:
   ```bash
   pip install -r requirements-app.txt
   ```

### Frontend Setup

1. **Navigate to mindmapper directory**:
   ```bash
   cd mindmapper
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Development mode**:
   ```bash
   npm run dev
   ```
   This starts the Vite dev server on port 5174.

4. **Production build**:
   ```bash
   npm run build
   ```
   This builds the React app and outputs to `app/static/mindmapper/`.

## Running the Application

### Development Mode

1. **Start the FastAPI backend** (from project root):
   ```bash
   python -m app.main
   # Or
   uvicorn app.main:app --reload
   ```

2. **Start the mindmapper frontend** (from `mindmapper/` directory):
   ```bash
   npm run dev
   ```

3. **Access the application**:
   - Navigate to `http://localhost:8000/brainstorm`
   - Click on "Mindmapper" card
   - Or directly: `http://localhost:8000/brainstorm/mindmapper`

### Production Mode

1. **Build the frontend**:
   ```bash
   cd mindmapper
   npm run build
   ```

2. **Start the backend**:
   ```bash
   python -m app.main
   ```

3. **Access the application**:
   - The built files are served from `app/static/mindmapper/`
   - Navigate to `http://localhost:8000/brainstorm/mindmapper`

## File Structure

```
mindmapper/
├── src/
│   ├── features/
│   │   └── mindmapper/
│   │       ├── components/
│   │       │   ├── Canvas.tsx          # Main canvas component
│   │       │   ├── Node.tsx            # Individual node component
│   │       │   ├── Toolbar.tsx         # Top toolbar
│   │       │   ├── Sidebar.tsx         # Left sidebar (mindmap list)
│   │       │   └── Inspector.tsx      # Right panel (node properties)
│   │       ├── hooks/
│   │       │   └── useMindmap.ts       # Mindmap state management hook
│   │       ├── utils/
│   │       │   ├── layout.ts           # Layout algorithms
│   │       │   └── export.ts           # Export functions
│   │       └── types.ts                # TypeScript type definitions
│   ├── lib/
│   │   └── api.ts                      # API client functions
│   ├── pages/
│   │   └── MindmapperPage.tsx          # Main page component
│   ├── App.tsx                         # App router
│   ├── main.tsx                        # Entry point
│   └── index.css                       # Global styles
├── package.json
├── vite.config.ts
└── tsconfig.json

app/
├── routes/
│   └── mindmaps.py                     # API routes
├── models.py                            # Database models (Mindmap, MindmapNode)
├── schemas.py                           # Pydantic schemas
└── static/
    └── mindmapper/                      # Built frontend files (after build)
```

## API Endpoints

All endpoints are under `/api/mindmaps`:

- `GET /api/mindmaps` - List all mind maps
- `GET /api/mindmaps/{id}` - Get a specific mind map
- `POST /api/mindmaps` - Create a new mind map
- `PUT /api/mindmaps/{id}` - Update a mind map
- `DELETE /api/mindmaps/{id}` - Delete a mind map
- `POST /api/mindmaps/{id}/nodes` - Create a node
- `PUT /api/mindmaps/{id}/nodes/{node_id}` - Update a node
- `DELETE /api/mindmaps/{id}/nodes/{node_id}` - Delete a node (and children)

## Usage Guide

### Creating a Mind Map

1. Click "New Mind Map" in the toolbar or sidebar
2. A new mind map is created with a central node
3. Start adding nodes by:
   - Double-clicking on empty canvas
   - Using keyboard shortcuts (Tab/Enter)
   - Using the Inspector panel buttons

### Editing Nodes

1. **Select a node**: Click on it
2. **Edit text**: Double-click the node or use the Inspector panel
3. **Change colors**: Use the color pickers in the Inspector
4. **Change shape**: Select from dropdown in Inspector
5. **Move node**: Drag the node (feature to be implemented)

### Organizing Nodes

- **Auto Layout**: Click the 📐 button to automatically arrange nodes in a radial layout
- **Center View**: Click the 🎯 button to center the view on the root node
- **Zoom**: Use mouse wheel or zoom controls

### Exporting

- **JSON**: Export the raw data structure
- **SVG**: Export as scalable vector graphics
- **PNG**: Export as raster image

## Integration with Existing App

The mindmapper is integrated into the brainstorming section:

1. **Navigation**: Added to `/brainstorm` page as a card
2. **Routing**: Accessible at `/brainstorm/mindmapper`
3. **Styling**: Uses existing Bootstrap theme and colors
4. **Authentication**: Currently uses optional `owner_id` (can be extended)

## Database Schema

### Mindmap Table
- `id`: UUID primary key
- `title`: String (default: "Untitled Mind Map")
- `owner_id`: Optional foreign key to users table
- `created_at`: Timestamp
- `updated_at`: Timestamp

### MindmapNode Table
- `id`: UUID primary key
- `mindmap_id`: Foreign key to mindmaps
- `parent_id`: Optional foreign key to parent node
- `x`, `y`: Integer coordinates
- `text`: Text content
- `color`: Hex color string
- `text_color`: Hex color string
- `shape`: Enum ('rect', 'pill')
- `width`, `height`: Optional integers (auto-calculated)
- `created_at`, `updated_at`: Timestamps

## Future Enhancements

1. **Templates**: Pre-built mind map templates
2. **Collaboration**: Real-time multi-user editing
3. **AI Integration**: AI-assisted idea expansion and organization
4. **Node Dragging**: Drag nodes to reposition
5. **Undo/Redo**: Full history stack with undo/redo
6. **Node Images**: Support for images in nodes
7. **Custom Connections**: Manual connections between any nodes
8. **Themes**: Pre-defined color themes
9. **Search**: Search nodes by text
10. **Keyboard Navigation**: Arrow keys to navigate between nodes

## Troubleshooting

### Frontend not loading
- Ensure Vite dev server is running (port 5174)
- Check browser console for errors
- Verify API proxy configuration in `vite.config.ts`

### API errors
- Check backend is running on port 8000
- Verify database tables are created
- Check CORS settings in `app/main.py`

### Build issues
- Clear `node_modules` and reinstall: `rm -rf node_modules && npm install`
- Check Node.js version: `node --version` (should be 18+)

## Testing

Run tests (when implemented):
```bash
cd mindmapper
npm test
```

## License

Same as the main project.

