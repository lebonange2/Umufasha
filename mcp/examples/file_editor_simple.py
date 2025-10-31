#!/usr/bin/env python3
"""Simple file editor using MCP coding environment tools."""
import sys
import json
import subprocess
from pathlib import Path

def send_request(method: str, params: dict) -> dict:
    """Send request to MCP server."""
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params
    }
    
    proc = subprocess.Popen(
        [sys.executable, "-m", "mcp.server", "--transport", "stdio"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=Path.cwd()
    )
    
    # Send request
    proc.stdin.write(json.dumps(request) + "\n")
    proc.stdin.flush()
    proc.stdin.close()
    
    # Read response
    response_line = proc.stdout.readline()
    response = json.loads(response_line)
    
    proc.wait()
    
    if "error" in response:
        raise Exception(f"Error: {response['error']}")
    
    return response.get("result", {})


def list_files(path: str = ".") -> list:
    """List files in directory."""
    result = send_request("tools/call", {
        "name": "listFiles",
        "arguments": {"path": path}
    })
    content = result.get("content", [{}])[0].get("text", "{}")
    data = json.loads(content) if content else {}
    return data.get("entries", [])


def read_file(path: str) -> str:
    """Read file content."""
    result = send_request("tools/call", {
        "name": "readFile",
        "arguments": {"path": path}
    })
    content = result.get("content", [{}])[0].get("text", "{}")
    data = json.loads(content) if content else {}
    if "error" in data:
        raise Exception(data["error"])
    return data.get("content", "")


def write_file(path: str, contents: str):
    """Write file content."""
    result = send_request("tools/call", {
        "name": "writeFile",
        "arguments": {
            "path": path,
            "contents": contents,
            "options": {"atomic": True}
        }
    })
    content = result.get("content", [{}])[0].get("text", "{}")
    data = json.loads(content) if content else {}
    if "error" in data:
        raise Exception(data["error"])


def main():
    """Simple file editor."""
    if len(sys.argv) < 2:
        print("Usage: python3 file_editor_simple.py <command> [args...]")
        print("\nCommands:")
        print("  ls [path]     - List files")
        print("  cat <file>    - Read file")
        print("  edit <file>   - Edit file")
        return
    
    command = sys.argv[1]
    
    try:
        if command == "ls":
            path = sys.argv[2] if len(sys.argv) > 2 else "."
            print(f"📂 {path}:")
            entries = list_files(path)
            for entry in entries:
                icon = "📁" if entry["type"] == "dir" else "📄"
                print(f"  {icon} {entry['name']}")
        
        elif command == "cat":
            if len(sys.argv) < 3:
                print("Usage: cat <file>")
                return
            file_path = sys.argv[2]
            content = read_file(file_path)
            print(content)
        
        elif command == "edit":
            if len(sys.argv) < 3:
                print("Usage: edit <file>")
                return
            file_path = sys.argv[2]
            
            # Read current content
            try:
                current = read_file(file_path)
                print(f"Current content of {file_path}:")
                print("-" * 60)
                print(current)
                print("-" * 60)
            except:
                current = ""
                print(f"Creating new file: {file_path}")
            
            # Get new content from stdin
            print("\nEnter new content (end with Ctrl+D or Ctrl+C):")
            new_lines = []
            try:
                while True:
                    line = input()
                    new_lines.append(line)
            except (EOFError, KeyboardInterrupt):
                pass
            
            new_content = "\n".join(new_lines)
            
            # Write file
            write_file(file_path, new_content)
            print(f"✅ File saved: {file_path}")
        
        else:
            print(f"Unknown command: {command}")
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

