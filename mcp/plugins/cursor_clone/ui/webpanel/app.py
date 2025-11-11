#!/usr/bin/env python3
"""Web panel for Cursor-AI Clone."""
from fastapi import FastAPI, Request, Form, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import json
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, List
import structlog

from mcp.plugins.cursor_clone.config import load_config, get_workspace_root
from mcp.plugins.cursor_clone.llm.engine import LLMEngineFactory
from mcp.plugins.cursor_clone.agent.repo_indexer import RepositoryIndexer
from mcp.plugins.cursor_clone.agent.planner import TaskPlanner
from mcp.plugins.cursor_clone.agent.editor import CodeEditor
from mcp.plugins.cursor_clone.agent.chat import ChatAssistant

logger = structlog.get_logger(__name__)

app = FastAPI(title="Cursor-AI Clone Web Panel")

# Global instances
_config = None
_cli = None


def get_cli():
    """Get CLI instance."""
    global _cli
    if _cli is None:
        global _config
        if _config is None:
            _config = load_config()
        _cli = CursorCLI(_config)
        # Initialize in background
        asyncio.create_task(_cli.initialize())
    return _cli


class CursorCLI:
    """CLI interface for Cursor-AI Clone."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize CLI."""
        self.config = config
        self.workspace_root = get_workspace_root(config)
        
        # Initialize components
        self.llm = LLMEngineFactory.create(config.get("llm", {}))
        self.indexer = RepositoryIndexer(self.workspace_root, config)
        self.planner = TaskPlanner(self.llm, config)
        self.editor = CodeEditor(self.workspace_root, config)
        self.chat = ChatAssistant(self.llm, self.indexer, config)
        self._initialized = False
    
    async def initialize(self):
        """Initialize components."""
        if self._initialized:
            return
        
        # Load LLM
        await self.llm.load()
        
        # Index repository if enabled
        if self.config.get("indexing", {}).get("enabled", True):
            logger.info("Indexing repository...")
            self.indexer.index_repository(full=True)
        
        self._initialized = True


@app.get("/", response_class=HTMLResponse)
async def index():
    """Main web panel page."""
    html = """<!DOCTYPE html>
<html>
<head>
    <title>Cursor-AI Clone</title>
    <style>
        body { font-family: monospace; margin: 0; padding: 20px; background: #1e1e1e; color: #d4d4d4; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: #2d2d2d; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .chat-area { background: #252526; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .messages { height: 400px; overflow-y: auto; margin-bottom: 20px; padding: 10px; background: #1e1e1e; border-radius: 4px; }
        .message { margin-bottom: 10px; padding: 10px; border-radius: 4px; }
        .user { background: #0e639c; }
        .assistant { background: #37373d; }
        .input-area { display: flex; gap: 10px; }
        .input-area input { flex: 1; padding: 10px; background: #3c3c3c; border: 1px solid #555; color: #d4d4d4; border-radius: 4px; }
        .input-area button { padding: 10px 20px; background: #0e639c; color: white; border: none; border-radius: 4px; cursor: pointer; }
        .input-area button:hover { background: #1177bb; }
        .file-tree { background: #252526; padding: 20px; border-radius: 8px; }
        .file-item { padding: 5px; cursor: pointer; }
        .file-item:hover { background: #37373d; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Cursor-AI Clone</h1>
            <p id="provider-info">AI coding assistant</p>
            <div style="margin-top: 10px;">
                <label>Provider: </label>
                <select id="provider-select" onchange="changeProvider()">
                    <option value="local">Local (gemma3:4b)</option>
                    <option value="openai">ChatGPT (OpenAI)</option>
                </select>
            </div>
        </div>
        
        <div class="chat-area">
            <h2>Chat</h2>
            <div id="messages" class="messages"></div>
            <div class="input-area">
                <input type="text" id="message-input" placeholder="Ask a question or request a change..." />
                <button onclick="sendMessage()">Send</button>
            </div>
        </div>
        
        <div class="file-tree">
            <h2>Workspace</h2>
            <div id="file-tree"></div>
        </div>
    </div>
    
    <script>
        const messagesDiv = document.getElementById('messages');
        const input = document.getElementById('message-input');
        
        function addMessage(role, content) {
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message ' + role;
            messageDiv.textContent = content;
            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }
        
        async function sendMessage() {
            const message = input.value.trim();
            if (!message) return;
            
            addMessage('user', message);
            input.value = '';
            
            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({messages: [{role: 'user', content: message}]})
                });
                
                const data = await response.json();
                if (data.error) {
                    addMessage('assistant', 'Error: ' + data.error);
                } else {
                    addMessage('assistant', data.assistant_message || data.response || 'No response');
                }
            } catch (error) {
                addMessage('assistant', 'Error: ' + error.message);
            }
        }
        
        input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
        
        // Load file tree
        fetch('/api/files')
            .then(r => r.json())
            .then(data => {
                const treeDiv = document.getElementById('file-tree');
                if (data.files) {
                    data.files.slice(0, 20).forEach(file => {
                        const item = document.createElement('div');
                        item.className = 'file-item';
                        item.textContent = file.name;
                        treeDiv.appendChild(item);
                    });
                }
            });
        
        // Load current provider
        fetch('/api/provider')
            .then(r => r.json())
            .then(data => {
                const select = document.getElementById('provider-select');
                const info = document.getElementById('provider-info');
                if (data.provider) {
                    select.value = data.provider;
                    updateProviderInfo(data.provider);
                }
            });
        
        function changeProvider() {
            const select = document.getElementById('provider-select');
            const provider = select.value;
            
            fetch('/api/provider', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({provider: provider})
            })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    updateProviderInfo(provider);
                    addMessage('system', 'Provider changed to ' + provider);
                }
            });
        }
        
        function updateProviderInfo(provider) {
            const info = document.getElementById('provider-info');
            if (provider === 'local') {
                info.textContent = 'Local AI coding assistant powered by gemma3:4b';
            } else {
                info.textContent = 'AI coding assistant powered by ChatGPT (OpenAI)';
            }
        }
    </script>
</body>
</html>"""
    return html


@app.post("/api/chat")
async def api_chat(request: Request):
    """Chat API endpoint."""
    try:
        data = await request.json()
        messages = data.get("messages", [])
        context_files = data.get("context_files")
        selection = data.get("selection")
        
        cli = get_cli()
        await cli.initialize()
        
        if not messages:
            return JSONResponse({"error": "messages required"})
        
        last_message = messages[-1].get("content", "") if messages else ""
        result = await cli.chat.chat(
            last_message,
            context_files=context_files,
            selection=selection
        )
        
        return JSONResponse({
            "assistant_message": result.get("response", ""),
            "citations": result.get("citations", [])
        })
    except Exception as e:
        logger.error("Error in chat API", error=str(e), exc_info=True)
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/api/plan")
async def api_plan(request: Request):
    """Plan API endpoint."""
    try:
        data = await request.json()
        goal = data.get("goal", "")
        scope = data.get("scope")
        files = data.get("files")
        constraints = data.get("constraints", {})
        
        if not goal:
            return JSONResponse({"error": "goal required"})
        
        cli = get_cli()
        await cli.initialize()
        
        plan_result = await cli.planner.plan(goal, scope=scope, files=files, constraints=constraints)
        
        return JSONResponse(plan_result)
    except Exception as e:
        logger.error("Error in plan API", error=str(e), exc_info=True)
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/files")
async def api_files():
    """List files API endpoint."""
    try:
        cli = get_cli()
        await cli.initialize()
        
        # Get file list from indexer
        files = []
        for file_path, file_info in cli.indexer.file_index.items():
            files.append({
                "name": file_path,
                "size": file_info.get("size", 0),
                "chunks": file_info.get("chunks", 0)
            })
        
        return JSONResponse({"files": files[:100]})  # Limit to 100
    except Exception as e:
        logger.error("Error listing files", error=str(e), exc_info=True)
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/provider")
async def api_get_provider():
    """Get current LLM provider."""
    try:
        config = load_config()
        provider = config.get("llm", {}).get("provider", "local")
        return JSONResponse({"provider": provider})
    except Exception as e:
        logger.error("Error getting provider", error=str(e), exc_info=True)
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/api/provider")
async def api_set_provider(request: Request):
    """Set LLM provider."""
    try:
        data = await request.json()
        provider = data.get("provider", "local")
        
        # Validate provider
        if provider not in ["local", "openai", "chatgpt"]:
            return JSONResponse({"error": "Invalid provider"}, status_code=400)
        
        # Set environment variable
        import os
        os.environ["LLM_PROVIDER"] = provider
        
        # Reload config and recreate CLI
        global _cli, _config
        _cli = None
        _config = None
        
        return JSONResponse({"success": True, "provider": provider})
    except Exception as e:
        logger.error("Error setting provider", error=str(e), exc_info=True)
        return JSONResponse({"error": str(e)}, status_code=500)


if __name__ == "__main__":
    config = load_config()
    port = config.get("ui", {}).get("port", 7701)
    
    # Ensure port is an integer
    if isinstance(port, str):
        port = int(port)
    
    print(f"Starting Cursor-AI Clone Web Panel on http://localhost:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)

