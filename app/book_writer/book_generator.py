"""Main class for generating books using LLM agents."""
import re
from typing import Dict, List, Optional
from app.book_writer.agents import BookAgents
from app.book_writer.config import get_config


class BookGenerator:
    """Generates complete books from outlines."""
    
    def __init__(self, agents: BookAgents, agent_config: Dict, outline: List[Dict]):
        """Initialize with outline to maintain chapter count context."""
        self.agents = agents
        self.agent_config = agent_config
        self.chapters_memory = []  # Store chapter summaries
        self.outline = outline  # Store the outline

    def _clean_chapter_content(self, content: str) -> str:
        """Clean up chapter content by removing artifacts and chapter numbers."""
        # Remove chapter number references
        content = re.sub(r'\*?\s*\(Chapter \d+.*?\)', '', content)
        content = re.sub(r'\*?\s*Chapter \d+.*?\n', '', content, count=1)
        
        # Clean up any remaining markdown artifacts
        content = content.replace('*', '')
        content = content.strip()
        
        return content

    def _extract_final_scene(self, content: str) -> Optional[str]:
        """Extract chapter content with improved content detection."""
        # Handle complete scene content
        if "SCENE FINAL:" in content:
            scene_text = content.split("SCENE FINAL:")[1].strip()
            if scene_text:
                return scene_text
                
        # Fallback to scene content
        if "SCENE:" in content:
            scene_text = content.split("SCENE:")[1].strip()
            if scene_text:
                return scene_text
                
        # Handle EDITED_SCENE
        if "EDITED_SCENE:" in content:
            scene_text = content.split("EDITED_SCENE:")[1].strip()
            if scene_text:
                return scene_text
        
        # Handle raw content
        if len(content.strip()) > 100:  # Minimum content threshold
            return content.strip()
            
        return None

    def _prepare_chapter_context(self, chapter_number: int, prompt: str) -> str:
        """Prepare context for chapter generation."""
        if chapter_number == 1:
            return f"Initial Chapter\nRequirements:\n{prompt}"
            
        context_parts = [
            "Previous Chapter Summaries:",
            *[f"Chapter {i+1}: {summary}" for i, summary in enumerate(self.chapters_memory)],
            "\nCurrent Chapter Requirements:",
            prompt
        ]
        return "\n".join(context_parts)

    async def generate_chapter(self, chapter_number: int, prompt: str) -> str:
        """Generate a single chapter with completion verification."""
        print(f"\nGenerating Chapter {chapter_number}...")
        
        try:
            # Prepare context
            context = self._prepare_chapter_context(chapter_number, prompt)
            
            # Step 1: Writer generates draft
            print(f"  Step 1: Writing draft...")
            chapter_draft = await self.agents.writer(chapter_number, prompt, context)
            
            # Step 2: Editor reviews
            print(f"  Step 2: Editing...")
            edited_chapter = await self.agents.editor(chapter_number, chapter_draft, prompt)
            
            # Extract final content
            final_content = self._extract_final_scene(edited_chapter)
            if not final_content:
                # Fallback to draft if edited version doesn't have proper markers
                final_content = self._extract_final_scene(chapter_draft)
            
            if not final_content:
                raise ValueError(f"No valid content found for Chapter {chapter_number}")
            
            # Clean content
            final_content = self._clean_chapter_content(final_content)
            
            # Step 3: Memory Keeper updates memory
            print(f"  Step 3: Updating memory...")
            memory_update = await self.agents.memory_keeper(chapter_number, final_content, self.chapters_memory)
            
            # Extract memory summary
            if "MEMORY UPDATE:" in memory_update:
                memory_summary = memory_update.split("MEMORY UPDATE:")[1].strip()
                # Take first 200 chars as summary
                memory_summary = memory_summary[:200] + "..." if len(memory_summary) > 200 else memory_summary
            else:
                # Create basic memory from chapter content
                memory_summary = f"Chapter {chapter_number} Summary: {final_content[:200]}..."
            
            self.chapters_memory.append(memory_summary)
            
            return final_content
            
        except Exception as e:
            print(f"Error in chapter {chapter_number}: {str(e)}")
            raise

    async def generate_book(self, outline: List[Dict]) -> Dict[str, any]:
        """Generate the book with strict chapter sequencing."""
        print("\nStarting Book Generation...")
        print(f"Total chapters: {len(outline)}")
        
        # Sort outline by chapter number
        sorted_outline = sorted(outline, key=lambda x: x["chapter_number"])
        
        chapters = {}
        
        for chapter in sorted_outline:
            chapter_number = chapter["chapter_number"]
            
            try:
                # Generate current chapter
                print(f"\n{'='*20} Chapter {chapter_number} {'='*20}")
                chapter_content = await self.generate_chapter(chapter_number, chapter["prompt"])
                
                chapters[str(chapter_number)] = {
                    "number": chapter_number,
                    "title": chapter["title"],
                    "content": chapter_content,
                    "prompt": chapter["prompt"]
                }
                
                print(f"✓ Chapter {chapter_number} complete")
                
            except Exception as e:
                print(f"Failed to generate chapter {chapter_number}: {str(e)}")
                # Continue with next chapter
                chapters[str(chapter_number)] = {
                    "number": chapter_number,
                    "title": chapter["title"],
                    "content": f"Error generating chapter: {str(e)}",
                    "prompt": chapter["prompt"],
                    "error": True
                }
        
        return {
            "outline": outline,
            "chapters": chapters,
            "total_chapters": len(outline),
            "completed_chapters": len([c for c in chapters.values() if not c.get("error", False)])
        }

