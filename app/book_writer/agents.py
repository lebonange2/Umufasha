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
            model=agent_config.get("model", "qwen3:30b"),
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
        """Outline creator agent - creates detailed chapter outlines with fully descriptive text."""
        system_message = f"""You are an expert story outline creator. Generate a complete, fully-filled {num_chapters}-chapter outline.

CRITICAL: Every element must have REAL, SPECIFIC, DESCRIPTIVE text - NO placeholders, NO generic labels.

FORMAT FOR EACH CHAPTER (use this EXACT structure):

Chapter 1: [A specific, descriptive chapter title that captures the chapter's main event]
Chapter Title: [Same as above]
Key Events:
- [Specific event 1 - a full sentence describing what happens]
- [Specific event 2 - a full sentence describing what happens]
- [Specific event 3 - a full sentence describing what happens]
Character Developments: [Specific description of how characters change or develop in this chapter]
Setting: [Specific location and atmosphere description]
Tone: [Specific emotional and narrative tone]

Sections:
Section 1: [A specific, descriptive section title - NOT "Section 1"]
- Subsection 1.1: [A specific, descriptive subsection title - NOT "Subsection 1.1"]
  Main Points:
  * [A FULL SENTENCE describing what happens in paragraph 1 - like "Introduce Daniel, a tired Earth engineer living in a collapsing megacity, who secretly dreams of the stars."]
  * [A FULL SENTENCE describing what happens in paragraph 2 - be specific and story-relevant]
  * [A FULL SENTENCE describing what happens in paragraph 3 - be specific and story-relevant]
- Subsection 1.2: [A specific, descriptive subsection title - NOT "Subsection 1.2"]
  Main Points:
  * [A FULL SENTENCE describing what happens in paragraph 1]
  * [A FULL SENTENCE describing what happens in paragraph 2]
  * [A FULL SENTENCE describing what happens in paragraph 3]
Section 2: [A specific, descriptive section title]
- Subsection 2.1: [A specific, descriptive subsection title]
  Main Points:
  * [A FULL SENTENCE describing what happens in paragraph 1]
  * [A FULL SENTENCE describing what happens in paragraph 2]
  * [A FULL SENTENCE describing what happens in paragraph 3]
- Subsection 2.2: [A specific, descriptive subsection title]
  Main Points:
  * [A FULL SENTENCE describing what happens in paragraph 1]
  * [A FULL SENTENCE describing what happens in paragraph 2]
  * [A FULL SENTENCE describing what happens in paragraph 3]
Section 3: [A specific, descriptive section title]
- Subsection 3.1: [A specific, descriptive subsection title]
  Main Points:
  * [A FULL SENTENCE describing what happens in paragraph 1]
  * [A FULL SENTENCE describing what happens in paragraph 2]
  * [A FULL SENTENCE describing what happens in paragraph 3]
- Subsection 3.2: [A specific, descriptive subsection title]
  Main Points:
  * [A FULL SENTENCE describing what happens in paragraph 1]
  * [A FULL SENTENCE describing what happens in paragraph 2]
  * [A FULL SENTENCE describing what happens in paragraph 3]

[REPEAT THIS EXACT FORMAT FOR ALL {num_chapters} CHAPTERS]

ABSOLUTE REQUIREMENTS:
1. Chapter titles: Must be specific and descriptive (e.g., "Exile to the Red World" NOT "Chapter 1")
2. Section titles: Must be specific and descriptive (e.g., "Leaving Earth" NOT "Section 1")
3. Subsection titles: Must be specific and descriptive (e.g., "The Offer from Mars" NOT "Subsection 1.1")
4. Main Points: MUST be FULL SENTENCES describing what happens in that paragraph
   - Example GOOD: "Introduce Daniel, a tired Earth engineer living in a collapsing megacity, who secretly dreams of the stars."
   - Example BAD: "Main point for paragraph 1" or "Character introduction"
5. Every main point must be a complete sentence (10+ words minimum)
6. All content must be story-specific based on the premise - do NOT use generic examples
7. NO placeholders, NO brackets, NO generic labels
8. Every chapter must have exactly 3 Sections
9. Every section must have exactly 2 Subsections
10. Every subsection must have exactly 3 Main Points

Initial Premise:
{initial_prompt}

START WITH 'OUTLINE:' AND END WITH 'END OF OUTLINE'"""
        
        user_prompt = f"""Create a complete {num_chapters}-chapter outline based on this premise.

Story Premise: {initial_prompt}

Story Arc:
{story_arc}

World Elements:
{world_elements}

CRITICAL INSTRUCTIONS:
1. Generate SPECIFIC, DESCRIPTIVE titles for every chapter, section, and subsection
2. For each main point, write a FULL SENTENCE (10+ words) describing what happens in that paragraph
3. Base all content on the story premise - make it relevant to the specific story
4. Every main point should read like: "Main point for paragraph 1: [full descriptive sentence]"
5. Do NOT use generic labels like "Section 1" or "Main point for paragraph 1" as the actual content
6. Make every element story-specific and detailed

Example of what main points should look like:
* Main point for paragraph 1: Introduce Daniel, a tired Earth engineer living in a collapsing megacity, who secretly dreams of the stars.
* Main point for paragraph 2: He receives a mysterious encrypted message inviting him to join an advanced Martian civilization that has watched Earth for decades.

Generate the complete outline now with FULLY FILLED content at every level."""
        
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
2. Follow the main points for each subsection/paragraph - write one paragraph for each main point
3. Maintain consistent character voices
4. Incorporate world-building details
5. Create engaging prose
6. Please make sure that you write the complete scene, do not leave it incomplete
7. Each chapter MUST be at least 5000 words (approximately 30,000 characters). Consider this a hard requirement. If your output is shorter, continue writing until you reach this minimum length
8. Ensure transitions are smooth and logical
9. Do not cut off the scene, make sure it has a proper ending
10. Add a lot of details, and describe the environment and characters where it makes sense
11. Structure your writing to follow the sections and subsections, with each main point becoming a paragraph

Always reference the outline and previous content, especially the main points for each subsection.
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

