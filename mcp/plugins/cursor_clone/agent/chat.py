"""Chat loop for interactive code assistance."""
from typing import List, Dict, Any, Optional, AsyncIterator
import structlog

from mcp.plugins.cursor_clone.llm.engine import LLMEngine
from mcp.plugins.cursor_clone.agent.repo_indexer import RepositoryIndexer

logger = structlog.get_logger(__name__)


class ChatAssistant:
    """Chat assistant for code-related questions."""
    
    def __init__(
        self,
        llm: LLMEngine,
        indexer: RepositoryIndexer,
        config: Dict[str, Any]
    ):
        """Initialize chat assistant."""
        self.llm = llm
        self.indexer = indexer
        self.config = config
        self.conversation_history: List[Dict[str, str]] = []
    
    async def chat(
        self,
        message: str,
        context_files: Optional[List[str]] = None,
        selection: Optional[str] = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        """Chat with the assistant."""
        logger.info("Chat request", message_length=len(message), context_files=context_files)
        
        # Build context from files if provided
        context = self._build_context(context_files, selection)
        
        # Build prompt
        prompt = self._build_prompt(message, context)
        
        # Get system prompt
        system_prompt = self._get_system_prompt()
        
        # Generate response (non-streaming for now)
        response = await self.llm.generate(prompt, system_prompt)
        
        # Update conversation history
        self.conversation_history.append({"role": "user", "content": message})
        self.conversation_history.append({"role": "assistant", "content": response})
        
        return {
            "response": response,
            "citations": self._extract_citations(response)
        }
    
    async def chat_stream(
        self,
        message: str,
        context_files: Optional[List[str]] = None,
        selection: Optional[str] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """Chat with the assistant (streaming)."""
        logger.info("Chat stream request", message_length=len(message), context_files=context_files)
        
        # Build context from files if provided
        context = self._build_context(context_files, selection)
        
        # Build prompt
        prompt = self._build_prompt(message, context)
        
        # Get system prompt
        system_prompt = self._get_system_prompt()
        
        # Stream response
        response = ""
        async for token in self.llm.stream(prompt, system_prompt):
            response += token
            yield {"token": token, "response": response}
        
        # Final yield with citations
        yield {"response": response, "citations": self._extract_citations(response), "done": True}
        
        # Update conversation history
        self.conversation_history.append({"role": "user", "content": message})
        self.conversation_history.append({"role": "assistant", "content": response})
    
    def _build_context(self, context_files: Optional[List[str]], selection: Optional[str]) -> str:
        """Build context from files and selection."""
        context_parts = []
        
        if selection:
            context_parts.append(f"Selected code:\n{selection}\n")
        
        if context_files:
            for file_path in context_files:
                file_context = self.indexer.get_file_context(file_path)
                if file_context:
                    context_parts.append(f"File: {file_path}\n")
                    # Add relevant chunks
                    for chunk in file_context.get("chunks", [])[:3]:
                        context_parts.append(f"Lines {chunk['start_line']}-{chunk['end_line']}:\n{chunk['content']}\n")
        
        return "\n".join(context_parts)
    
    def _build_prompt(self, message: str, context: str) -> str:
        """Build prompt from message and context."""
        prompt_parts = []
        
        if context:
            prompt_parts.append(context)
        
        prompt_parts.append(f"\nUser question: {message}")
        
        return "\n".join(prompt_parts)
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for chat."""
        return """You are a helpful coding assistant. You help with:
- Explaining code
- Refactoring suggestions
- Writing tests
- Documentation
- Code optimization

Follow these principles:
- Be clear and concise
- Provide code examples when helpful
- Reference specific files and lines when relevant
- Suggest best practices
- Consider testing and maintainability"""
    
    def _extract_citations(self, response: str) -> List[Dict[str, Any]]:
        """Extract citations from response."""
        citations = []
        
        # Simple heuristic: look for file references
        import re
        file_pattern = r"([a-zA-Z0-9_/.-]+\.(py|js|ts|java|cpp|go|rs|rb|php|swift|kt|scala|md|txt|json|yaml|yml|toml|xml|html|css|scss|less|sh|bash|zsh|sql|r|m|lua|vim|el|clj|hs))"
        
        for match in re.finditer(file_pattern, response):
            file_path = match.group(1)
            citations.append({
                "type": "file",
                "path": file_path,
                "context": match.group(0)
            })
        
        return citations
    
    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history.clear()

