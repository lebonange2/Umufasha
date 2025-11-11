"""Repository indexer for local code embeddings and RAG."""
import os
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
import fnmatch
import structlog
from dataclasses import dataclass
from datetime import datetime

logger = structlog.get_logger(__name__)


@dataclass
class CodeChunk:
    """Represents a chunk of code for indexing."""
    file_path: str
    start_line: int
    end_line: int
    content: str
    chunk_id: str
    metadata: Dict[str, Any]


class RepositoryIndexer:
    """Indexes repository for semantic search and RAG."""
    
    def __init__(self, workspace_root: Path, config: Dict[str, Any]):
        """Initialize repository indexer."""
        self.workspace_root = workspace_root.resolve()
        self.config = config
        self.index_config = config.get("indexing", {})
        self.ignore_patterns = self.index_config.get("ignore_patterns", [])
        self.chunk_size = self.index_config.get("chunk_size", 1000)
        self.chunk_overlap = self.index_config.get("chunk_overlap", 200)
        self.index: Dict[str, CodeChunk] = {}
        self.file_index: Dict[str, Dict[str, Any]] = {}
        self.symbol_index: Dict[str, List[Dict[str, Any]]] = {}
    
    def should_ignore(self, path: Path) -> bool:
        """Check if path should be ignored."""
        rel_path = str(path.relative_to(self.workspace_root))
        
        for pattern in self.ignore_patterns:
            if fnmatch.fnmatch(rel_path, pattern) or fnmatch.fnmatch(str(path), pattern):
                return True
        
        return False
    
    def index_repository(self, full: bool = False) -> Dict[str, Any]:
        """Index the repository."""
        logger.info("Starting repository indexing", workspace=str(self.workspace_root), full=full)
        
        if full:
            self.index.clear()
            self.file_index.clear()
            self.symbol_index.clear()
        
        indexed_files = 0
        indexed_chunks = 0
        
        # Walk through repository
        for root, dirs, files in os.walk(self.workspace_root):
            # Filter directories
            dirs[:] = [d for d in dirs if not self.should_ignore(Path(root) / d)]
            
            for file in files:
                file_path = Path(root) / file
                
                if self.should_ignore(file_path):
                    continue
                
                # Only index text files
                if not self._is_text_file(file_path):
                    continue
                
                try:
                    chunks = self._index_file(file_path)
                    if chunks:
                        indexed_files += 1
                        indexed_chunks += len(chunks)
                except Exception as e:
                    logger.warning("Failed to index file", file=str(file_path), error=str(e))
        
        stats = {
            "files_indexed": indexed_files,
            "chunks_indexed": indexed_chunks,
            "total_chunks": len(self.index),
            "total_files": len(self.file_index)
        }
        
        logger.info("Repository indexing complete", **stats)
        return stats
    
    def _is_text_file(self, path: Path) -> bool:
        """Check if file is a text file."""
        # Simple heuristic: check extension
        text_extensions = {
            ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".cpp", ".c", ".h",
            ".go", ".rs", ".rb", ".php", ".swift", ".kt", ".scala",
            ".md", ".txt", ".json", ".yaml", ".yml", ".toml", ".xml",
            ".html", ".css", ".scss", ".less", ".sh", ".bash", ".zsh",
            ".sql", ".r", ".m", ".lua", ".vim", ".el", ".clj", ".hs"
        }
        
        return path.suffix.lower() in text_extensions
    
    def _index_file(self, file_path: Path) -> List[CodeChunk]:
        """Index a single file."""
        rel_path = str(file_path.relative_to(self.workspace_root))
        
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception as e:
            logger.warning("Failed to read file", file=str(file_path), error=str(e))
            return []
        
        # Chunk the file
        chunks = self._chunk_file(rel_path, content)
        
        # Store file metadata
        self.file_index[rel_path] = {
            "path": rel_path,
            "size": len(content),
            "lines": content.count("\n") + 1,
            "chunks": len(chunks),
            "indexed_at": datetime.now().isoformat()
        }
        
        # Extract symbols (simple heuristic for now)
        symbols = self._extract_symbols(rel_path, content)
        if symbols:
            self.symbol_index[rel_path] = symbols
        
        return chunks
    
    def _chunk_file(self, file_path: str, content: str) -> List[CodeChunk]:
        """Chunk file content into smaller pieces."""
        lines = content.splitlines()
        chunks = []
        
        start = 0
        while start < len(lines):
            end = min(start + self.chunk_size, len(lines))
            chunk_lines = lines[start:end]
            chunk_content = "\n".join(chunk_lines)
            
            # Create chunk ID
            chunk_id = hashlib.sha256(
                f"{file_path}:{start}:{end}".encode()
            ).hexdigest()[:16]
            
            chunk = CodeChunk(
                file_path=file_path,
                start_line=start + 1,
                end_line=end,
                content=chunk_content,
                chunk_id=chunk_id,
                metadata={
                    "file": file_path,
                    "start": start + 1,
                    "end": end,
                    "size": len(chunk_content)
                }
            )
            
            chunks.append(chunk)
            self.index[chunk_id] = chunk
            
            # Move start with overlap
            start = end - self.chunk_overlap
        
        return chunks
    
    def _extract_symbols(self, file_path: str, content: str) -> List[Dict[str, Any]]:
        """Extract symbols (functions, classes, etc.) from file."""
        symbols = []
        lines = content.splitlines()
        
        # Simple regex-based extraction for Python
        import re
        
        # Functions
        func_pattern = r"^def\s+(\w+)\s*\("
        for i, line in enumerate(lines, 1):
            match = re.match(func_pattern, line.strip())
            if match:
                symbols.append({
                    "name": match.group(1),
                    "type": "function",
                    "line": i,
                    "file": file_path
                })
        
        # Classes
        class_pattern = r"^class\s+(\w+)"
        for i, line in enumerate(lines, 1):
            match = re.match(class_pattern, line.strip())
            if match:
                symbols.append({
                    "name": match.group(1),
                    "type": "class",
                    "line": i,
                    "file": file_path
                })
        
        return symbols
    
    def search_code(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Search code using simple text matching (RAG would use embeddings)."""
        query_lower = query.lower()
        results = []
        
        # Simple text search across chunks
        for chunk_id, chunk in self.index.items():
            if query_lower in chunk.content.lower():
                results.append({
                    "chunk_id": chunk_id,
                    "file": chunk.file_path,
                    "start_line": chunk.start_line,
                    "end_line": chunk.end_line,
                    "content": chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content,
                    "score": chunk.content.lower().count(query_lower)
                })
        
        # Sort by score and limit
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:max_results]
    
    def find_symbol(self, symbol_name: str) -> List[Dict[str, Any]]:
        """Find symbol by name."""
        results = []
        
        for file_path, symbols in self.symbol_index.items():
            for symbol in symbols:
                if symbol_name.lower() in symbol["name"].lower():
                    results.append(symbol)
        
        return results
    
    def get_file_context(self, file_path: str, line: Optional[int] = None) -> Dict[str, Any]:
        """Get context for a file."""
        rel_path = str(Path(file_path).relative_to(self.workspace_root))
        
        if rel_path not in self.file_index:
            return {}
        
        file_info = self.file_index[rel_path].copy()
        
        # Get chunks for this file
        file_chunks = [
            chunk for chunk in self.index.values()
            if chunk.file_path == rel_path
        ]
        
        file_info["chunks"] = [
            {
                "start_line": chunk.start_line,
                "end_line": chunk.end_line,
                "content": chunk.content[:500] + "..." if len(chunk.content) > 500 else chunk.content
            }
            for chunk in file_chunks
        ]
        
        # Get symbols for this file
        if rel_path in self.symbol_index:
            file_info["symbols"] = self.symbol_index[rel_path]
        
        return file_info

