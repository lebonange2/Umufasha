#!/usr/bin/env python3
"""Simple CLI client for coding environment tools via MCP server."""
import asyncio
import json
import sys
from pathlib import Path
from typing import Optional

# Simple MCP client over stdio
class SimpleMCPClient:
    def __init__(self):
        self.request_id = 0
        self.process = None
        self.stdout_queue = asyncio.Queue()
        self.stderr_queue = asyncio.Queue()
    
    async def connect(self):
        """Connect to MCP server via stdio."""
        self.process = await asyncio.create_subprocess_exec(
            sys.executable, "-m", "mcp.server", "--transport", "stdio",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=Path.cwd()
        )
        
        # Start reading stdout
        asyncio.create_task(self._read_stdout())
        asyncio.create_task(self._read_stderr())
        
        # Initialize
        await self.request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "coding-env-client", "version": "1.0.0"}
        })
        
        # Send initialized notification
        await self.notify("initialized", {})
    
    async def _read_stdout(self):
        """Read stdout and queue messages."""
        while True:
            line = await self.process.stdout.readline()
            if not line:
                break
            line_str = line.decode("utf-8").rstrip("\n\r")
            if line_str:
                try:
                    await self.stdout_queue.put(json.loads(line_str))
                except:
                    pass
    
    async def _read_stderr(self):
        """Read stderr."""
        while True:
            line = await self.process.stderr.readline()
            if not line:
                break
            print(f"STDERR: {line.decode('utf-8')}", file=sys.stderr)
    
    async def request(self, method: str, params: Optional[dict] = None) -> dict:
        """Send request and wait for response."""
        self.request_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
            "params": params or {}
        }
        
        # Send request
        request_str = json.dumps(request) + "\n"
        self.process.stdin.write(request_str.encode("utf-8"))
        await self.process.stdin.drain()
        
        # Wait for response
        while True:
            message = await self.stdout_queue.get()
            if message.get("id") == self.request_id:
                if "error" in message:
                    raise Exception(f"Error: {message['error']}")
                return message.get("result", {})
    
    async def notify(self, method: str, params: Optional[dict] = None):
        """Send notification."""
        notification = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params or {}
        }
        request_str = json.dumps(notification) + "\n"
        self.process.stdin.write(request_str.encode("utf-8"))
        await self.process.stdin.drain()
    
    async def call_tool(self, name: str, arguments: dict) -> dict:
        """Call a tool."""
        result = await self.request("tools/call", {
            "name": name,
            "arguments": arguments
        })
        return result
    
    async def list_files(self, path: str = ".", recursive: bool = False) -> list:
        """List files in directory."""
        result = await self.call_tool("listFiles", {
            "path": path,
            "options": {"recursive": recursive}
        })
        content = result.get("content", [{}])[0].get("text", "{}")
        data = json.loads(content) if content else {}
        return data.get("entries", [])
    
    async def read_file(self, path: str) -> dict:
        """Read file content."""
        result = await self.call_tool("readFile", {"path": path})
        content = result.get("content", [{}])[0].get("text", "{}")
        return json.loads(content) if content else {}
    
    async def write_file(self, path: str, contents: str) -> dict:
        """Write file content."""
        result = await self.call_tool("writeFile", {
            "path": path,
            "contents": contents,
            "options": {"atomic": True}
        })
        return result
    
    async def search_files(self, query: str, globs: Optional[list] = None) -> list:
        """Search for text in files."""
        options = {}
        if globs:
            options["globs"] = globs
        result = await self.call_tool("searchFiles", {
            "query": query,
            "options": options
        })
        content = result.get("content", [{}])[0].get("text", "{}")
        data = json.loads(content) if content else {}
        return data.get("results", [])
    
    async def disconnect(self):
        """Disconnect from MCP server."""
        if self.process:
            self.process.stdin.close()
            await self.process.wait()


async def interactive_mode(client: SimpleMCPClient):
    """Interactive file browser/editor."""
    current_path = "."
    
    while True:
        print("\n" + "="*60)
        print(f"📁 Current Directory: {current_path}")
        print("="*60)
        print("\nCommands:")
        print("  ls [path]          - List files")
        print("  cat <file>         - Read file")
        print("  edit <file>        - Edit file")
        print("  search <query>     - Search for text")
        print("  cd <path>          - Change directory (not implemented)")
        print("  exit               - Exit")
        
        try:
            cmd = input("\n> ").strip()
            if not cmd:
                continue
            
            parts = cmd.split()
            command = parts[0]
            
            if command == "exit":
                break
            elif command == "ls":
                path = parts[1] if len(parts) > 1 else current_path
                print(f"\n📂 Listing: {path}")
                entries = await client.list_files(path)
                for entry in entries[:50]:  # Limit to 50 entries
                    icon = "📁" if entry["type"] == "dir" else "📄"
                    size = f"{entry['size']:,} bytes" if entry.get("size") else ""
                    print(f"  {icon} {entry['name']:<40} {size}")
                if len(entries) > 50:
                    print(f"  ... and {len(entries) - 50} more")
            
            elif command == "cat":
                if len(parts) < 2:
                    print("Usage: cat <file>")
                    continue
                file_path = parts[1]
                print(f"\n📄 Reading: {file_path}")
                file_data = await client.read_file(file_path)
                if "error" in file_data:
                    print(f"Error: {file_data['error']}")
                else:
                    content = file_data.get("content", "")
                    if file_data.get("isBinary"):
                        print(f"[Binary file, {file_data.get('size', 0)} bytes]")
                    else:
                        print("-" * 60)
                        print(content)
                        print("-" * 60)
            
            elif command == "edit":
                if len(parts) < 2:
                    print("Usage: edit <file>")
                    continue
                file_path = parts[1]
                
                # Read current content
                print(f"\n📝 Editing: {file_path}")
                file_data = await client.read_file(file_path)
                if "error" in file_data:
                    # File doesn't exist, create new
                    current_content = ""
                    print("File doesn't exist, creating new file.")
                else:
                    current_content = file_data.get("content", "")
                    if file_data.get("isBinary"):
                        print("Cannot edit binary file.")
                        continue
                
                print("\nCurrent content:")
                print("-" * 60)
                print(current_content)
                print("-" * 60)
                print("\nEnter new content (end with 'EOF' on a new line):")
                
                # Read multi-line input
                lines = []
                while True:
                    line = input()
                    if line.strip() == "EOF":
                        break
                    lines.append(line)
                
                new_content = "\n".join(lines)
                
                # Write file
                result = await client.write_file(file_path, new_content)
                if "error" in result:
                    print(f"Error writing file: {result['error']}")
                else:
                    print(f"✅ File written: {file_path}")
            
            elif command == "search":
                if len(parts) < 2:
                    print("Usage: search <query>")
                    continue
                query = " ".join(parts[1:])
                print(f"\n🔍 Searching for: '{query}'")
                results = await client.search_files(query, options={"maxResults": 20})
                if not results:
                    print("No results found.")
                else:
                    for result in results:
                        print(f"  {result['path']}:{result['line']}: {result['text'][:80]}")
            
            else:
                print(f"Unknown command: {command}")
        
        except KeyboardInterrupt:
            print("\n\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}")


async def main():
    """Main entry point."""
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        client = SimpleMCPClient()
        await client.connect()
        try:
            await interactive_mode(client)
        finally:
            await client.disconnect()
    else:
        print("Usage: python3 coding_env_client.py --interactive")
        print("\nThis will start an interactive file browser/editor")
        print("that uses the MCP server's coding environment tools.")


if __name__ == "__main__":
    asyncio.run(main())

