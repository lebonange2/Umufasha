"""MCP tools for Cursor-AI Clone."""
from typing import Dict, Any, Optional, List
from pathlib import Path
import structlog

from mcp.capabilities.tools.base import FunctionTool
from mcp.core.concurrency import CancellationToken

from mcp.plugins.cursor_clone.config import load_config, get_workspace_root
from mcp.plugins.cursor_clone.llm.engine import LLMEngine, LLMEngineFactory
from mcp.plugins.cursor_clone.agent.repo_indexer import RepositoryIndexer
from mcp.plugins.cursor_clone.agent.planner import TaskPlanner
from mcp.plugins.cursor_clone.agent.editor import CodeEditor
from mcp.plugins.cursor_clone.agent.chat import ChatAssistant

logger = structlog.get_logger(__name__)

# Global instances (initialized on first use)
_config = None
_llm = None
_indexer = None
_planner = None
_editor = None
_chat = None


def _get_config() -> Dict[str, Any]:
    """Get configuration."""
    global _config
    if _config is None:
        _config = load_config()
    return _config


def _get_llm() -> LLMEngine:
    """Get LLM engine."""
    global _llm
    if _llm is None:
        config = _get_config()
        _llm = LLMEngineFactory.create(config.get("llm", {}))
        # Model will be loaded on first use (lazy loading)
    return _llm


async def _ensure_llm_loaded():
    """Ensure LLM is loaded."""
    llm = _get_llm()
    if not llm.is_loaded():
        await llm.load()


def _get_indexer() -> RepositoryIndexer:
    """Get repository indexer."""
    global _indexer
    if _indexer is None:
        config = _get_config()
        workspace_root = get_workspace_root(config)
        _indexer = RepositoryIndexer(workspace_root, config)
    return _indexer


def _get_planner() -> TaskPlanner:
    """Get task planner."""
    global _planner
    if _planner is None:
        config = _get_config()
        llm = _get_llm()
        _planner = TaskPlanner(llm, config)
    return _planner


def _get_editor() -> CodeEditor:
    """Get code editor."""
    global _editor
    if _editor is None:
        config = _get_config()
        workspace_root = get_workspace_root(config)
        _editor = CodeEditor(workspace_root, config)
    return _editor


def _get_chat() -> ChatAssistant:
    """Get chat assistant."""
    global _chat
    if _chat is None:
        config = _get_config()
        llm = _get_llm()
        indexer = _get_indexer()
        _chat = ChatAssistant(llm, indexer, config)
    return _chat


async def plan_and_patch_tool(
    params: Dict[str, Any],
    cancellation_token: Optional[CancellationToken] = None
) -> Dict[str, Any]:
    """Plan and generate patch for a goal."""
    if cancellation_token:
        cancellation_token.check()
    
    goal = params.get("goal", "")
    scope = params.get("scope")
    files = params.get("files")
    constraints = params.get("constraints", {})
    
    if not goal:
        return {"error": "goal is required"}
    
    try:
        # Ensure LLM is loaded
        await _ensure_llm_loaded()
        
        planner = _get_planner()
        plan_result = await planner.plan(goal, scope, files, constraints)
        
        # For now, return plan (in production, would also generate diff)
        return {
            "plan": plan_result.get("plan", {}),
            "risks": plan_result.get("risks", []),
            "steps": plan_result.get("steps", 0),
            "complexity": plan_result.get("estimated_complexity", "unknown"),
            "diff": ""  # Would be generated in production
        }
    except Exception as e:
        logger.error("Error in plan_and_patch", error=str(e), exc_info=True)
        return {"error": str(e)}


async def apply_patch_tool(
    params: Dict[str, Any],
    cancellation_token: Optional[CancellationToken] = None
) -> Dict[str, Any]:
    """Apply a patch."""
    if cancellation_token:
        cancellation_token.check()
    
    diff = params.get("diff", "")
    message = params.get("message", "AI: Applied patch")
    dry_run = params.get("dry_run", False)
    
    if not diff:
        return {"error": "diff is required"}
    
    try:
        editor = _get_editor()
        result = editor.apply_patch_string(diff, dry_run=dry_run)
        
        # Auto-commit if configured
        git_commit = None
        config = _get_config()
        if config.get("git", {}).get("auto_commit", False) and not dry_run:
            # Would create git commit here
            pass
        
        return {
            "status": result.get("status"),
            "files_affected": result.get("files_affected", 0),
            "git_commit": git_commit
        }
    except Exception as e:
        logger.error("Error applying patch", error=str(e), exc_info=True)
        return {"error": str(e)}


async def rollback_last_tool(
    params: Dict[str, Any],
    cancellation_token: Optional[CancellationToken] = None
) -> Dict[str, Any]:
    """Rollback last changes."""
    if cancellation_token:
        cancellation_token.check()
    
    steps = params.get("steps", 1)
    file_path = params.get("file_path")
    git_commit = params.get("git_commit")
    
    try:
        editor = _get_editor()
        
        if file_path:
            result = editor.rollback_file(file_path, git_commit)
            return result
        else:
            # Would rollback multiple files
            return {"error": "file_path or git_commit required"}
    except Exception as e:
        logger.error("Error rolling back", error=str(e), exc_info=True)
        return {"error": str(e)}


async def chat_tool(
    params: Dict[str, Any],
    cancellation_token: Optional[CancellationToken] = None
) -> Dict[str, Any]:
    """Chat with the assistant."""
    if cancellation_token:
        cancellation_token.check()
    
    messages = params.get("messages", [])
    selection = params.get("selection")
    context_files = params.get("context_files")
    stream = params.get("stream", False)
    
    if not messages:
        return {"error": "messages are required"}
    
    # Get last user message
    last_message = messages[-1].get("content", "") if messages else ""
    
    try:
        # Ensure LLM is loaded
        await _ensure_llm_loaded()
        
        chat = _get_chat()
        
        if stream:
            # For streaming, we'd need to handle it differently in MCP
            # For now, return non-streaming
            result = await chat.chat(
                last_message,
                context_files=context_files,
                selection=selection,
                stream=False
            )
        else:
            result = await chat.chat(
                last_message,
                context_files=context_files,
                selection=selection,
                stream=False
            )
        
        return {
            "assistant_message": result.get("response", ""),
            "citations": result.get("citations", [])
        }
    except Exception as e:
        logger.error("Error in chat", error=str(e), exc_info=True)
        return {"error": str(e)}


async def run_tests_tool(
    params: Dict[str, Any],
    cancellation_token: Optional[CancellationToken] = None
) -> Dict[str, Any]:
    """Run tests."""
    if cancellation_token:
        cancellation_token.check()
    
    suite = params.get("suite")
    pattern = params.get("pattern")
    
    try:
        from mcp.plugins.cursor_clone.exec.runner import CommandRunner
        config = _get_config()
        workspace_root = get_workspace_root(config)
        runner = CommandRunner(workspace_root, config)
        
        result = await runner.run_tests(suite=suite, pattern=pattern)
        
        return {
            "summary": result.get("summary", {}),
            "framework": result.get("framework", "unknown"),
            "exit_code": result.get("exit_code", 0),
            "logs_path": "logs/test_results.log"
        }
    except Exception as e:
        logger.error("Error running tests", error=str(e), exc_info=True)
        return {"error": str(e)}


async def index_refresh_tool(
    params: Dict[str, Any],
    cancellation_token: Optional[CancellationToken] = None
) -> Dict[str, Any]:
    """Refresh repository index."""
    if cancellation_token:
        cancellation_token.check()
    
    full = params.get("full", False)
    
    try:
        indexer = _get_indexer()
        stats = indexer.index_repository(full=full)
        return stats
    except Exception as e:
        logger.error("Error refreshing index", error=str(e), exc_info=True)
        return {"error": str(e)}


async def search_code_tool(
    params: Dict[str, Any],
    cancellation_token: Optional[CancellationToken] = None
) -> Dict[str, Any]:
    """Search code in repository."""
    if cancellation_token:
        cancellation_token.check()
    
    query = params.get("query", "")
    max_results = params.get("max_results", 10)
    
    if not query:
        return {"error": "query is required"}
    
    try:
        indexer = _get_indexer()
        results = indexer.search_code(query, max_results=max_results)
        return {"matches": results}
    except Exception as e:
        logger.error("Error searching code", error=str(e), exc_info=True)
        return {"error": str(e)}


# Export tools
CURSOR_PLAN_AND_PATCH_TOOL = FunctionTool(
    name="cursor.planAndPatch",
    description="Plan and generate patch for a coding goal",
    input_schema={
        "type": "object",
        "properties": {
            "goal": {"type": "string", "description": "Goal to achieve"},
            "scope": {"type": "string", "description": "Scope of changes"},
            "files": {"type": "array", "items": {"type": "string"}, "description": "Files to consider"},
            "constraints": {"type": "object", "description": "Constraints"}
        },
        "required": ["goal"]
    },
    handler=plan_and_patch_tool
)

CURSOR_APPLY_PATCH_TOOL = FunctionTool(
    name="cursor.applyPatch",
    description="Apply a patch (diff)",
    input_schema={
        "type": "object",
        "properties": {
            "diff": {"type": "string", "description": "Unified diff to apply"},
            "message": {"type": "string", "description": "Commit message"},
            "dry_run": {"type": "boolean", "description": "Dry run mode"}
        },
        "required": ["diff"]
    },
    handler=apply_patch_tool
)

CURSOR_ROLLBACK_LAST_TOOL = FunctionTool(
    name="cursor.rollbackLast",
    description="Rollback last changes",
    input_schema={
        "type": "object",
        "properties": {
            "steps": {"type": "integer", "description": "Number of steps to rollback"},
            "file_path": {"type": "string", "description": "File to rollback"},
            "git_commit": {"type": "string", "description": "Git commit to restore"}
        }
    },
    handler=rollback_last_tool
)

CURSOR_CHAT_TOOL = FunctionTool(
    name="cursor.chat",
    description="Chat with the coding assistant",
    input_schema={
        "type": "object",
        "properties": {
            "messages": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "role": {"type": "string"},
                        "content": {"type": "string"}
                    }
                },
                "description": "Conversation messages"
            },
            "selection": {"type": "string", "description": "Selected code"},
            "context_files": {"type": "array", "items": {"type": "string"}, "description": "Context files"}
        },
        "required": ["messages"]
    },
    handler=chat_tool
)

CURSOR_RUN_TESTS_TOOL = FunctionTool(
    name="cursor.runTests",
    description="Run tests",
    input_schema={
        "type": "object",
        "properties": {
            "suite": {"type": "string", "description": "Test suite"},
            "pattern": {"type": "string", "description": "Test pattern"}
        }
    },
    handler=run_tests_tool
)

CURSOR_INDEX_REFRESH_TOOL = FunctionTool(
    name="cursor.indexRefresh",
    description="Refresh repository index",
    input_schema={
        "type": "object",
        "properties": {
            "full": {"type": "boolean", "description": "Full reindex"}
        }
    },
    handler=index_refresh_tool
)

CURSOR_SEARCH_CODE_TOOL = FunctionTool(
    name="cursor.searchCode",
    description="Search code in repository",
    input_schema={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query"},
            "max_results": {"type": "integer", "description": "Maximum results"}
        },
        "required": ["query"]
    },
    handler=search_code_tool
)

