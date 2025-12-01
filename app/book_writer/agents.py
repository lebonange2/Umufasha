"""Define the agents used in the book generation system."""
from typing import Dict, List, Optional
from app.book_writer.config import get_config
from app.llm.client import LLMClient


class BookAgents:
    """Manages book generation agents using the existing LLM client."""
    
    def __init__(self, agent_config: Dict, outline: Optional[List[Dict]] = None):
        """Initialize agents with book outline context."""
        self.agent_config = agent_config
        self.outline = outline
        self.world_elements = {}
        self.character_developments = {}
        
        # Create LLM client
        self.llm_client = LLMClient(
            api_key=None,
            base_url=agent_config.get("base_url", "http://localhost:11434/v1"),
            model=agent_config.get("model", "llama3:latest"),
            provider=agent_config.get("provider", "local")
        )
        
    def _format_outline_context(self) -> str:
        """Format the book outline into a readable context."""
        if not self.outline:
            return ""
            
        context_parts = ["Complete Book Outline:"]
        for chapter in self.outline:
            context_parts.extend([
                f"\nChapter {chapter['chapter_number']}: {chapter['title']}",
                chapter['prompt']
            ])
        return "\n".join(context_parts)

    async def story_planner(self, initial_prompt: str) -> str:
        """Story planner agent - creates high-level story arc."""
        system_message = """You are an expert story arc planner focused on overall narrative structure.

Your sole responsibility is creating the high-level story arc.
When given an initial story premise:
1. Identify major plot points and story beats
2. Map character arcs and development
3. Note major story transitions
4. Plan narrative pacing

Format your output EXACTLY as:
STORY_ARC:
- Major Plot Points:
[List each major event that drives the story]

- Character Arcs:
[For each main character, describe their development path]

- Story Beats:
[List key emotional and narrative moments in sequence]

- Key Transitions:
[Describe major shifts in story direction or tone]

Always provide specific, detailed content - never use placeholders."""
        
        user_prompt = f"Create a story arc for this premise:\n\n{initial_prompt}"
        
        response = await self.llm_client.complete(system=system_message, user=user_prompt)
        return response

    async def world_builder(self, story_arc: str) -> str:
        """World builder agent - creates and maintains the story setting."""
        outline_context = self._format_outline_context()
        
        system_message = f"""You are an expert in world-building who creates rich, consistent settings.

Your role is to establish ALL settings and locations needed for the entire story based on a provided story arc.

Book Overview:
{outline_context}

Your responsibilities:
1. Review the story arc to identify every location and setting needed
2. Create detailed descriptions for each setting, including:
- Physical layout and appearance
- Atmosphere and environmental details
- Important objects or features
- Sensory details (sights, sounds, smells)
3. Identify recurring locations that appear multiple times
4. Note how settings might change over time
5. Create a cohesive world that supports the story's themes

Format your response as:
WORLD_ELEMENTS:

[LOCATION NAME]:
- Physical Description: [detailed description]
- Atmosphere: [mood, time of day, lighting, etc.]
- Key Features: [important objects, layout elements]
- Sensory Details: [what characters would experience]

[RECURRING ELEMENTS]:
- List any settings that appear multiple times
- Note any changes to settings over time

[TRANSITIONS]:
- How settings connect to each other
- How characters move between locations"""
        
        user_prompt = f"Create world elements for this story arc:\n\n{story_arc}"
        
        response = await self.llm_client.complete(system=system_message, user=user_prompt)
        return response

    async def outline_creator(self, initial_prompt: str, story_arc: str, world_elements: str, num_chapters: int) -> str:
        """Outline creator agent - creates detailed chapter outlines."""
        system_message = f"""Generate a detailed {num_chapters}-chapter outline.

YOU MUST USE EXACTLY THIS FORMAT FOR EACH CHAPTER - NO DEVIATIONS:

Chapter 1: [Title]
Chapter Title: [Same title as above]
Key Events:
- [Event 1]
- [Event 2]
- [Event 3]
Character Developments: [Specific character moments and changes]
Setting: [Specific location and atmosphere]
Tone: [Specific emotional and narrative tone]

[REPEAT THIS EXACT FORMAT FOR ALL {num_chapters} CHAPTERS]

Requirements:
1. EVERY field must be present for EVERY chapter
2. EVERY chapter must have AT LEAST 3 specific Key Events
3. ALL chapters must be detailed - no placeholders
4. Format must match EXACTLY - including all headings and bullet points

Initial Premise:
{initial_prompt}

START WITH 'OUTLINE:' AND END WITH 'END OF OUTLINE'"""
        
        user_prompt = f"""Create a {num_chapters}-chapter outline.

Story Arc:
{story_arc}

World Elements:
{world_elements}

Generate the complete outline now."""
        
        response = await self.llm_client.complete(system=system_message, user=user_prompt)
        return response

    async def memory_keeper(self, chapter_number: int, chapter_content: str, previous_summaries: List[str]) -> str:
        """Memory keeper agent - maintains story continuity."""
        outline_context = self._format_outline_context()
        
        system_message = f"""You are the keeper of the story's continuity and context.
Your responsibilities:
1. Track and summarize each chapter's key events
2. Monitor character development and relationships
3. Maintain world-building consistency
4. Flag any continuity issues

Book Overview:
{outline_context}

Format your responses as follows:
- Start updates with 'MEMORY UPDATE:'
- List key events with 'EVENT:'
- List character developments with 'CHARACTER:'
- List world details with 'WORLD:'
- Flag issues with 'CONTINUITY ALERT:'"""
        
        previous_context = "\n".join([f"Chapter {i+1}: {summary}" for i, summary in enumerate(previous_summaries)])
        
        user_prompt = f"""Update memory for Chapter {chapter_number}:

Previous Chapter Summaries:
{previous_context}

Current Chapter Content:
{chapter_content}

Provide a memory update."""
        
        response = await self.llm_client.complete(system=system_message, user=user_prompt)
        return response

    async def writer(self, chapter_number: int, chapter_prompt: str, context: str) -> str:
        """Writer agent - generates the actual prose."""
        outline_context = self._format_outline_context()
        
        system_message = f"""You are an expert creative writer who brings scenes to life.

Book Context:
{outline_context}

Your focus:
1. Write according to the outlined plot points
2. Maintain consistent character voices
3. Incorporate world-building details
4. Create engaging prose
5. Please make sure that you write the complete scene, do not leave it incomplete
6. Each chapter MUST be at least 5000 words (approximately 30,000 characters). Consider this a hard requirement. If your output is shorter, continue writing until you reach this minimum length
7. Ensure transitions are smooth and logical
8. Do not cut off the scene, make sure it has a proper ending
9. Add a lot of details, and describe the environment and characters where it makes sense

Always reference the outline and previous content.
Mark drafts with 'SCENE:' and final versions with 'SCENE FINAL:'"""
        
        user_prompt = f"""Write Chapter {chapter_number}:

Chapter Requirements:
{chapter_prompt}

Previous Context:
{context}

Write the complete chapter now. Mark it with 'SCENE FINAL:'"""
        
        response = await self.llm_client.complete(system=system_message, user=user_prompt)
        return response

    async def editor(self, chapter_number: int, chapter_content: str, chapter_prompt: str) -> str:
        """Editor agent - reviews and improves content."""
        outline_context = self._format_outline_context()
        
        system_message = f"""You are an expert editor ensuring quality and consistency.

Book Overview:
{outline_context}

Your focus:
1. Check alignment with outline
2. Verify character consistency
3. Maintain world-building rules
4. Improve prose quality
5. Return complete edited chapter
6. Never ask to start the next chapter, as the next step is finalizing this chapter
7. Each chapter MUST be at least 5000 words. If the content is shorter, return it to the writer for expansion. This is a hard requirement - do not approve chapters shorter than 5000 words

Format your responses:
1. Start critiques with 'FEEDBACK:'
2. Provide suggestions with 'SUGGEST:'
3. Return full edited chapter with 'EDITED_SCENE:'

Reference specific outline elements in your feedback."""
        
        user_prompt = f"""Edit Chapter {chapter_number}:

Chapter Requirements:
{chapter_prompt}

Current Chapter Content:
{chapter_content}

Review and provide feedback, then return the complete edited chapter."""
        
        response = await self.llm_client.complete(system=system_message, user=user_prompt)
        return response

