"""Search and grep operations."""
import re
from pathlib import Path
from typing import Dict, Any, List, Optional
import structlog

from cws.internal.policy.loader import Policy

logger = structlog.get_logger(__name__)


class SearchOperations:
    """Search and grep operations."""
    
    def __init__(self, workspace_root: Path, policy: Policy):
        """Initialize search operations."""
        self.workspace_root = workspace_root.resolve()
        self.policy = policy
    
    async def find(self, query: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Search for text in files."""
        options = options or {}
        use_regex = options.get("regex", False)
        case_sensitive = options.get("caseSensitive", False)
        globs = options.get("globs", ["**/*"])
        max_results = options.get("maxResults", 1000)
        
        # Compile pattern
        if use_regex:
            flags = 0 if case_sensitive else re.IGNORECASE
            pattern = re.compile(query, flags)
        else:
            # Escape special regex characters
            escaped = re.escape(query)
            flags = 0 if case_sensitive else re.IGNORECASE
            pattern = re.compile(escaped, flags)
        
        results = []
        count = 0
        
        # Match globs
        import fnmatch
        for pattern_str in globs:
            for file_path in self.workspace_root.rglob(pattern_str.replace("**", "*")):
                if count >= max_results:
                    break
                
                # Check policy
                try:
                    rel_path = str(file_path.relative_to(self.workspace_root))
                    if not self.policy.is_path_allowed(rel_path, self.workspace_root):
                        continue
                except ValueError:
                    continue
                
                # Skip directories
                if not file_path.is_file():
                    continue
                
                # Try to read and search
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                        lines = content.splitlines()
                        
                        for line_num, line in enumerate(lines, 1):
                            if pattern.search(line):
                                results.append({
                                    "path": rel_path,
                                    "line": line_num,
                                    "column": pattern.search(line).start() + 1,
                                    "text": line.strip()
                                })
                                count += 1
                                
                                if count >= max_results:
                                    break
                except Exception as e:
                    logger.debug("Failed to search file", path=rel_path, error=str(e))
                    continue
        
        return {"query": query, "results": results, "count": len(results)}
    
    async def symbols(self, scope: str, query: Optional[str] = None) -> Dict[str, Any]:
        """Find symbols (simplified implementation)."""
        # Simplified symbol search - can be enhanced with proper parsers
        # For now, search for common patterns like functions, classes
        symbols = []
        
        patterns = [
            (r"^def\s+(\w+)\s*\(", "function"),
            (r"^class\s+(\w+)", "class"),
            (r"^const\s+(\w+)\s*=", "constant"),
            (r"^let\s+(\w+)\s*=", "variable"),
            (r"^var\s+(\w+)\s*=", "variable"),
        ]
        
        if scope == "workspace":
            search_paths = list(self.workspace_root.rglob("*.py")) + \
                          list(self.workspace_root.rglob("*.js")) + \
                          list(self.workspace_root.rglob("*.ts"))
        else:
            # Single file
            file_path = self.workspace_root / scope
            if file_path.exists() and file_path.is_file():
                search_paths = [file_path]
            else:
                return {"scope": scope, "symbols": [], "count": 0}
        
        for file_path in search_paths:
            try:
                rel_path = str(file_path.relative_to(self.workspace_root))
                if not self.policy.is_path_allowed(rel_path, self.workspace_root):
                    continue
                
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    lines = content.splitlines()
                    
                    for line_num, line in enumerate(lines, 1):
                        for pattern, symbol_type in patterns:
                            match = re.search(pattern, line)
                            if match:
                                symbol_name = match.group(1)
                                if query is None or query.lower() in symbol_name.lower():
                                    symbols.append({
                                        "name": symbol_name,
                                        "type": symbol_type,
                                        "path": rel_path,
                                        "line": line_num
                                    })
            except Exception as e:
                logger.debug("Failed to parse file", path=str(file_path), error=str(e))
                continue
        
        return {"scope": scope, "symbols": symbols, "count": len(symbols)}

