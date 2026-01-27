# Coding Environment Frontend

React-based frontend for the Coding Environment integrated into the main FastAPI application.

## Features

- **File Browser**: Navigate and browse workspace files
- **Code Editor**: Monaco Editor with syntax highlighting for multiple languages
- **Terminal**: Execute commands in the workspace
- **Service Management**: Start/stop CWS and MCP Server services
- **WebSocket Integration**: Real-time communication with CWS and MCP Server

## Development

### Prerequisites

- Node.js 18+
- npm or yarn

### Setup

```bash
cd coding-environment-frontend
npm install
```

### Run Development Server

```bash
npm run dev
```

The frontend will be available at `http://localhost:5175` and proxied through the main FastAPI app at `/coding_environment`.

### Build for Production

```bash
npm run build
```

This will build the frontend and output to `app/static/coding-environment/` for serving by FastAPI.

## Architecture

- **Services**: WebSocket clients and API clients for CWS and MCP Server
- **Components**: Reusable UI components (FileBrowser, CodeEditor, Terminal, ServiceStatusPanel)
- **Pages**: Main CodingEnvironmentPage that orchestrates all components

## Integration

The coding environment is integrated into the main FastAPI application:

- Backend routes: `/api/coding-environment/*`
- Frontend route: `/coding_environment`
- WebSocket proxies: `/ws/mcp` and `/ws/cws`
