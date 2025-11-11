#!/usr/bin/env python3
"""CLI/TUI interface for Cursor-AI Clone."""
import asyncio
import sys
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
import argparse
import structlog

from mcp.plugins.cursor_clone.config import load_config, get_workspace_root
from mcp.plugins.cursor_clone.llm.engine import LLMEngineFactory
from mcp.plugins.cursor_clone.agent.repo_indexer import RepositoryIndexer
from mcp.plugins.cursor_clone.agent.planner import TaskPlanner
from mcp.plugins.cursor_clone.agent.editor import CodeEditor
from mcp.plugins.cursor_clone.agent.chat import ChatAssistant

logger = structlog.get_logger(__name__)


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
    
    async def initialize(self):
        """Initialize components."""
        # Load LLM
        await self.llm.load()
        
        # Index repository if enabled
        if self.config.get("indexing", {}).get("enabled", True):
            logger.info("Indexing repository...")
            self.indexer.index_repository(full=True)
    
    async def chat_mode(self, files: Optional[List[str]] = None, question: Optional[str] = None):
        """Interactive chat mode."""
        print("=" * 60)
        print("Cursor-AI Clone - Chat Mode")
        print("=" * 60)
        print(f"Workspace: {self.workspace_root}")
        print("Type 'exit' to quit, 'clear' to clear history")
        print("=" * 60)
        print()
        
        while True:
            try:
                if question:
                    user_input = question
                    question = None  # Use only once
                else:
                    user_input = input("You: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() == "exit":
                    break
                
                if user_input.lower() == "clear":
                    self.chat.clear_history()
                    print("History cleared.")
                    continue
                
                # Chat with assistant
                print("\nAssistant: ", end="", flush=True)
                result = await self.chat.chat(user_input, context_files=files)
                response = result.get("response", "")
                print(response)
                
                # Show citations if any
                citations = result.get("citations", [])
                if citations:
                    print("\nCitations:")
                    for citation in citations:
                        print(f"  - {citation.get('path', 'unknown')}")
                
                print()
            
            except KeyboardInterrupt:
                print("\n\nExiting...")
                break
            except Exception as e:
                print(f"Error: {e}")
                logger.error("Error in chat", error=str(e), exc_info=True)
    
    async def plan_and_patch_mode(self, goal: str, scope: Optional[str] = None):
        """Plan and patch mode."""
        print("=" * 60)
        print("Cursor-AI Clone - Plan & Patch Mode")
        print("=" * 60)
        print(f"Goal: {goal}")
        if scope:
            print(f"Scope: {scope}")
        print("=" * 60)
        print()
        
        # Create plan
        print("Creating plan...")
        plan_result = await self.planner.plan(goal, scope=scope)
        
        plan = plan_result.get("plan", {})
        risks = plan_result.get("risks", [])
        
        print("\nPlan:")
        print("-" * 60)
        print(plan.get("description", ""))
        print("-" * 60)
        
        if risks:
            print("\nRisks:")
            for risk in risks:
                print(f"  ⚠️  {risk}")
        
        print("\nSteps:")
        for i, step in enumerate(plan.get("steps", []), 1):
            print(f"\n{i}. {step.get('description', '')}")
            for detail in step.get("details", []):
                print(f"   {detail}")
        
        # Ask for confirmation
        print("\n" + "=" * 60)
        confirm = input("Apply this plan? (yes/no): ").strip().lower()
        
        if confirm == "yes":
            print("\nApplying plan...")
            # In production, would generate and apply diff here
            print("✓ Plan applied (dry-run mode)")
        else:
            print("Plan cancelled.")
    
    async def index_mode(self, full: bool = False):
        """Index repository."""
        print("Indexing repository...")
        stats = self.indexer.index_repository(full=full)
        print(f"✓ Indexed {stats.get('files_indexed', 0)} files")
        print(f"✓ Created {stats.get('chunks_indexed', 0)} chunks")
        print(f"✓ Total chunks: {stats.get('total_chunks', 0)}")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Cursor-AI Clone CLI")
    parser.add_argument("--config", type=Path, help="Config file path")
    parser.add_argument("--provider", choices=["local", "openai", "chatgpt"], help="LLM provider (local or openai/chatgpt)")
    parser.add_argument("--index", action="store_true", help="Index repository")
    parser.add_argument("--index-full", action="store_true", help="Full reindex")
    parser.add_argument("--chat", action="store_true", help="Start chat mode")
    parser.add_argument("--files", nargs="+", help="Context files for chat")
    parser.add_argument("--question", help="Question for chat")
    parser.add_argument("--plan", help="Plan and patch mode")
    parser.add_argument("--scope", help="Scope for plan")
    
    args = parser.parse_args()
    
    # Override provider if specified
    if args.provider:
        import os
        os.environ["LLM_PROVIDER"] = args.provider
    
    # Load config
    config = load_config(args.config)
    
    # Create CLI
    cli = CursorCLI(config)
    await cli.initialize()
    
    # Handle commands
    if args.index or args.index_full:
        await cli.index_mode(full=args.index_full)
    elif args.plan:
        await cli.plan_and_patch_mode(args.plan, scope=args.scope)
    elif args.chat or args.question:
        await cli.chat_mode(files=args.files, question=args.question)
    else:
        # Default to chat mode
        await cli.chat_mode()


if __name__ == "__main__":
    asyncio.run(main())

