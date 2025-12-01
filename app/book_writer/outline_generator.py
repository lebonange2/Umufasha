"""Generate book outlines using LLM agents."""
import re
from typing import Dict, List
from app.book_writer.agents import BookAgents
from app.book_writer.config import get_config


class OutlineGenerator:
    """Generates book outlines from initial prompts."""
    
    def __init__(self, agents: BookAgents, agent_config: Dict):
        self.agents = agents
        self.agent_config = agent_config

    async def generate_outline(self, initial_prompt: str, num_chapters: int = 25) -> List[Dict]:
        """Generate a book outline based on initial prompt."""
        print("\nGenerating outline...")

        try:
            # Step 1: Story Planner
            print("Step 1: Creating story arc...")
            story_arc = await self.agents.story_planner(initial_prompt)
            
            # Step 2: World Builder
            print("Step 2: Building world...")
            world_elements = await self.agents.world_builder(story_arc)
            
            # Step 3: Outline Creator
            print("Step 3: Creating detailed outline...")
            outline_text = await self.agents.outline_creator(initial_prompt, story_arc, world_elements, num_chapters)
            
            # Extract and process the outline
            return await self._process_outline_results(outline_text, num_chapters)
            
        except Exception as e:
            print(f"Error generating outline: {str(e)}")
            # Try to salvage any outline content we can find
            return await self._emergency_outline_processing(outline_text if 'outline_text' in locals() else "", num_chapters)

    async def _process_outline_results(self, outline_content: str, num_chapters: int) -> List[Dict]:
        """Extract and process the outline with strict format requirements."""
        if not outline_content:
            print("No structured outline found, attempting emergency processing...")
            return await self._emergency_outline_processing(outline_content, num_chapters)

        chapters = []
        
        # Extract content between OUTLINE: and END OF OUTLINE
        start_idx = outline_content.find("OUTLINE:")
        end_idx = outline_content.find("END OF OUTLINE")
        
        if start_idx != -1:
            if end_idx != -1:
                outline_content = outline_content[start_idx:end_idx]
            else:
                outline_content = outline_content[start_idx:]
        
        # Split by chapter markers
        chapter_sections = re.split(r'Chapter \d+:', outline_content)
        
        for i, section in enumerate(chapter_sections[1:], 1):  # Skip first empty section
            try:
                # Extract required components
                title_match = re.search(r'\*?\*?Title:\*?\*?\s*(.+?)(?=\n|$)', section, re.IGNORECASE)
                events_match = re.search(r'\*?\*?Key Events:\*?\*?\s*(.*?)(?=\*?\*?Character Developments:|$)', section, re.DOTALL | re.IGNORECASE)
                character_match = re.search(r'\*?\*?Character Developments:\*?\*?\s*(.*?)(?=\*?\*?Setting:|$)', section, re.DOTALL | re.IGNORECASE)
                setting_match = re.search(r'\*?\*?Setting:\*?\*?\s*(.*?)(?=\*?\*?Tone:|$)', section, re.DOTALL | re.IGNORECASE)
                tone_match = re.search(r'\*?\*?Tone:\*?\*?\s*(.*?)(?=\*?\*?Chapter \d+:|$)', section, re.DOTALL | re.IGNORECASE)

                # If no explicit title match, try to get it from the chapter header
                if not title_match:
                    title_match = re.search(r'\*?\*?Chapter \d+:\s*(.+?)(?=\n|$)', section)

                # Verify all components exist
                if not all([title_match, events_match, character_match, setting_match, tone_match]):
                    print(f"Missing required components in Chapter {i}")
                    missing = []
                    if not title_match: missing.append("Title")
                    if not events_match: missing.append("Key Events")
                    if not character_match: missing.append("Character Developments")
                    if not setting_match: missing.append("Setting")
                    if not tone_match: missing.append("Tone")
                    print(f"  Missing: {', '.join(missing)}")
                    continue

                # Format chapter content
                chapter_info = {
                    "chapter_number": i,
                    "title": title_match.group(1).strip(),
                    "prompt": "\n".join([
                        f"- Key Events: {events_match.group(1).strip()}",
                        f"- Character Developments: {character_match.group(1).strip()}",
                        f"- Setting: {setting_match.group(1).strip()}",
                        f"- Tone: {tone_match.group(1).strip()}"
                    ])
                }
                
                # Verify events (at least 3)
                events = re.findall(r'-\s*(.+?)(?=\n|$)', events_match.group(1))
                if len(events) < 3:
                    print(f"Chapter {i} has fewer than 3 events")
                    continue

                chapters.append(chapter_info)

            except Exception as e:
                print(f"Error processing Chapter {i}: {str(e)}")
                continue

        # If we don't have enough valid chapters, create placeholders
        if len(chapters) < num_chapters:
            print(f"Only processed {len(chapters)} valid chapters, creating placeholders for remaining...")
            chapters = await self._verify_chapter_sequence(chapters, num_chapters)

        return chapters

    async def _verify_chapter_sequence(self, chapters: List[Dict], num_chapters: int) -> List[Dict]:
        """Verify and fix chapter numbering."""
        # Sort chapters by their current number
        chapters.sort(key=lambda x: x['chapter_number'])
        
        # Renumber chapters sequentially starting from 1
        for i, chapter in enumerate(chapters, 1):
            chapter['chapter_number'] = i
        
        # Add placeholder chapters if needed
        while len(chapters) < num_chapters:
            next_num = len(chapters) + 1
            chapters.append({
                'chapter_number': next_num,
                'title': f'Chapter {next_num}',
                'prompt': '- Key events: [To be determined]\n- Character developments: [To be determined]\n- Setting: [To be determined]\n- Tone: [To be determined]'
            })
        
        # Trim excess chapters if needed
        chapters = chapters[:num_chapters]
        
        return chapters

    async def _emergency_outline_processing(self, outline_content: str, num_chapters: int) -> List[Dict]:
        """Emergency processing when normal outline extraction fails."""
        print("Attempting emergency outline processing...")
        
        chapters = []
        current_chapter = None
        
        # Look through content for any chapter markers
        lines = outline_content.split('\n')
        
        for line in lines:
            # Look for chapter markers
            chapter_match = re.search(r'Chapter (\d+)', line)
            if chapter_match and "Key events:" in outline_content:
                if current_chapter:
                    chapters.append(current_chapter)
                
                current_chapter = {
                    'chapter_number': int(chapter_match.group(1)),
                    'title': line.split(':')[-1].strip() if ':' in line else f"Chapter {chapter_match.group(1)}",
                    'prompt': []
                }
            
            # Collect bullet points
            if current_chapter and line.strip().startswith('-'):
                current_chapter['prompt'].append(line.strip())
        
        # Add the last chapter if it exists
        if current_chapter and current_chapter.get('prompt'):
            current_chapter['prompt'] = '\n'.join(current_chapter['prompt'])
            chapters.append(current_chapter)
        
        if not chapters:
            print("Emergency processing failed to find any chapters")
            # Create a basic outline structure
            chapters = [
                {
                    'chapter_number': i,
                    'title': f'Chapter {i}',
                    'prompt': '- Key events: [To be determined]\n- Character developments: [To be determined]\n- Setting: [To be determined]\n- Tone: [To be determined]'
                }
                for i in range(1, num_chapters + 1)
            ]
        
        # Ensure proper sequence and number of chapters
        return await self._verify_chapter_sequence(chapters, num_chapters)

