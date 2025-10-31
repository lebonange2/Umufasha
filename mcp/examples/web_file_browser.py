#!/usr/bin/env python3
"""Simple web-based file browser using MCP coding environment tools."""
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import json
import subprocess
import sys
from pathlib import Path

app = FastAPI(title="Coding Environment File Browser")

# Store current directory
current_dir = {"path": "."}


# Global MCP process (persistent connection)
_mcp_process = None
_request_id = 0


def _get_mcp_connection():
    """Get or create MCP connection."""
    global _mcp_process
    
    if _mcp_process is None or _mcp_process.poll() is not None:
        # Create new connection
        try:
            _mcp_process = subprocess.Popen(
                [sys.executable, "-m", "mcp.server", "--transport", "stdio"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=Path.cwd(),
                bufsize=1  # Line buffered
            )
            
            # Initialize connection
            init_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "web-file-browser", "version": "1.0.0"}
                }
            }
            
            _mcp_process.stdin.write(json.dumps(init_request) + "\n")
            _mcp_process.stdin.flush()
            
            # Read initialize response (wait for it)
            import time
            time.sleep(0.1)  # Small delay to ensure response is ready
            init_response = _mcp_process.stdout.readline()
            
            if not init_response:
                # Try again
                time.sleep(0.2)
                init_response = _mcp_process.stdout.readline()
            
            if not init_response:
                raise Exception("Failed to initialize MCP connection")
            
            # Send initialized notification
            notify = {"jsonrpc": "2.0", "method": "initialized", "params": {}}
            try:
                _mcp_process.stdin.write(json.dumps(notify) + "\n")
                _mcp_process.stdin.flush()
                time.sleep(0.05)  # Small delay after notification
            except (BrokenPipeError, OSError):
                # Process might have closed, recreate
                _mcp_process = None
                return _get_mcp_connection()
        except Exception as e:
            print(f"Error creating MCP connection: {e}", file=sys.stderr)
            _mcp_process = None
            raise
    
    return _mcp_process


def send_request(method: str, params: dict) -> dict:
    """Send request to MCP server."""
    global _request_id, _mcp_process
    
    try:
        proc = _get_mcp_connection()
        _request_id += 1
        current_id = _request_id
        
        request = {
            "jsonrpc": "2.0",
            "id": current_id,
            "method": method,
            "params": params
        }
        
        # Send request
        try:
            proc.stdin.write(json.dumps(request) + "\n")
            proc.stdin.flush()
        except (BrokenPipeError, OSError):
            # Connection broken, recreate
            _mcp_process = None
            proc = _get_mcp_connection()
            proc.stdin.write(json.dumps(request) + "\n")
            proc.stdin.flush()
        
        # Read response (skip any notifications)
        import time
        max_attempts = 10
        attempt = 0
        
        while attempt < max_attempts:
            # Small delay to allow response to be ready
            time.sleep(0.05)
            
            if proc.poll() is not None:
                # Process died, recreate connection
                _mcp_process = None
                return {"error": "MCP process died, please retry"}
            
            response_line = proc.stdout.readline()
            
            if not response_line:
                attempt += 1
                continue
            
            try:
                response = json.loads(response_line.strip())
                if "id" in response and response["id"] == current_id:
                    if "error" in response:
                        return {"error": response["error"]}
                    return response.get("result", {})
                # Skip notifications and other responses
            except json.JSONDecodeError:
                attempt += 1
                continue
            
            attempt += 1
        
        return {"error": "Timeout waiting for response"}
    except Exception as e:
        _mcp_process = None  # Reset connection on error
        return {"error": f"Request failed: {str(e)}"}


def list_files(path: str = ".") -> list:
    """List files in directory."""
    result = send_request("tools/call", {
        "name": "listFiles",
        "arguments": {"path": path, "workspaceRoot": "."}
    })
    if "error" in result:
        print(f"Error in list_files: {result['error']}", file=sys.stderr)
        return []
    
    content_list = result.get("content", [])
    if not content_list:
        print("No content in result", file=sys.stderr)
        return []
    
    content_text = content_list[0].get("text", "{}")
    if not content_text:
        print("Empty content text", file=sys.stderr)
        return []
    
    try:
        data = json.loads(content_text)
        entries = data.get("entries", [])
        print(f"Found {len(entries)} entries", file=sys.stderr)
        return entries
    except json.JSONDecodeError as e:
        print(f"Failed to parse content: {e}", file=sys.stderr)
        print(f"Content: {content_text[:200]}", file=sys.stderr)
        return []


def read_file(path: str) -> dict:
    """Read file content."""
    result = send_request("tools/call", {
        "name": "readFile",
        "arguments": {"path": path, "workspaceRoot": "."}
    })
    if "error" in result:
        return {"error": result["error"]}
    content_list = result.get("content", [])
    if not content_list:
        return {"error": "No content in response"}
    content_text = content_list[0].get("text", "{}")
    try:
        return json.loads(content_text) if content_text else {}
    except json.JSONDecodeError as e:
        return {"error": f"Failed to parse file data: {e}"}


def write_file(path: str, contents: str) -> dict:
    """Write file content."""
    result = send_request("tools/call", {
        "name": "writeFile",
        "arguments": {
            "workspaceRoot": ".",
            "path": path,
            "contents": contents,
            "options": {"atomic": True}
        }
    })
    if "error" in result:
        return {"error": result["error"]}
    content_list = result.get("content", [])
    if not content_list:
        return {"error": "No content in response"}
    content_text = content_list[0].get("text", "{}")
    try:
        return json.loads(content_text) if content_text else {}
    except json.JSONDecodeError as e:
        return {"error": f"Failed to parse response: {e}"}


@app.get("/read")
async def read_file_endpoint(path: str):
    """Read file endpoint."""
    file_data = read_file(path)
    if "error" in file_data:
        return {"error": file_data["error"]}
    
    if file_data.get("isBinary"):
        return {"error": "Cannot display binary file", "isBinary": True}
    
    return {
        "path": file_data.get("path"),
        "content": file_data.get("content", ""),
        "size": file_data.get("size"),
        "mtime": file_data.get("mtime")
    }


@app.post("/save")
async def save_file(path: str = Form(...), contents: str = Form(...)):
    """Save file endpoint."""
    result = write_file(path, contents)
    if "error" in result:
        return HTMLResponse(f"<h2>Error</h2><p>{result['error']}</p><p><a href='/'>Back</a></p>")
    
    return HTMLResponse(f"<h2>File Saved</h2><p>File {path} saved successfully.</p><p><a href='/'>Back</a></p>")


@app.get("/", response_class=HTMLResponse)
async def index(path: str = "."):
    """Main file browser page with path parameter."""
    current_dir["path"] = path
    entries = list_files(path)
    
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>File Browser - Coding Environment</title>
    <style>
        body {{ font-family: monospace; margin: 20px; }}
        .header {{ background: #f0f0f0; padding: 10px; margin-bottom: 20px; }}
        .file-list {{ border: 1px solid #ccc; padding: 10px; }}
        .file-item {{ padding: 5px; cursor: pointer; }}
        .file-item:hover {{ background: #f0f0f0; }}
        .dir {{ color: #0066cc; }}
        .file {{ color: #333; }}
        .editor {{ width: 100%; height: 500px; font-family: monospace; }}
        .button {{ padding: 5px 15px; margin: 5px; cursor: pointer; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📁 File Browser - Coding Environment</h1>
        <p>Current Path: <strong>{path}</strong></p>
    </div>
    <div class="file-list">
        <h2>Files and Directories</h2>
"""
    
    # Add parent directory link
    if path != ".":
        parent = str(Path(path).parent) if Path(path).parent != Path(".") else "."
        html += f'<div class="file-item dir" onclick="location.href=\'/?path={parent}\'">📁 .. (parent)</div>'
    
    for entry in entries[:100]:
        icon = "📁" if entry["type"] == "dir" else "📄"
        name = entry["name"]
        entry_path = entry["path"]
        if entry["type"] == "dir":
            html += f'<div class="file-item dir" onclick="location.href=\'/?path={entry_path}\'">{icon} {name}</div>'
        else:
            html += f'<div class="file-item file" onclick="openFile(\'{entry_path}\')">{icon} {name}</div>'
    
    html += """
    </div>
    
    <div id="editor" style="display:none; margin-top:20px;">
        <h2>File Editor</h2>
        <form method="post" action="/save">
            <input type="hidden" id="file-path" name="path" value="">
            <textarea id="file-content" name="contents" class="editor"></textarea>
            <br>
            <button type="submit" class="button">Save</button>
            <button type="button" class="button" onclick="closeEditor()">Close</button>
        </form>
    </div>
    
    <script>
        function openFile(path) {
            fetch('/read?path=' + encodeURIComponent(path))
                .then(r => r.json())
                .then(data => {
                    if (data.error) {
                        alert('Error: ' + data.error);
                    } else {
                        document.getElementById('file-path').value = path;
                        document.getElementById('file-content').value = data.content || '';
                        document.getElementById('editor').style.display = 'block';
                        window.scrollTo(0, document.body.scrollHeight);
                    }
                });
        }
        
        function closeEditor() {
            document.getElementById('editor').style.display = 'none';
        }
    </script>
</body>
</html>
"""
    
    return html


if __name__ == "__main__":
    print("Starting File Browser on http://localhost:8001")
    print("Access it in your browser!")
    uvicorn.run(app, host="0.0.0.0", port=8001)
