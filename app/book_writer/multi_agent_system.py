"""
Multi-Agent Book Generation System

This module implements a Manager-Writer agentic system for automated book generation.
The Manager agent plans, supervises, and reviews, while the Writer agent generates content.

Author: AI Systems Engineer
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import json
from app.llm.client import LLMClient
from app.book_writer.config import get_config


class MessageRole(Enum):
    """Roles in the agent communication protocol."""
    MANAGER = "manager"
    WRITER = "writer"


@dataclass
class AgentMessage:
    """Message protocol between agents."""
    role: MessageRole
    task: str
    context_summary: str
    constraints: Dict[str, Any]
    expected_output_format: str
    feedback: Optional[str] = None  # For revision requests


@dataclass
class BookState:
    """Global state maintained by the Manager agent."""
    title: str
    premise: str
    target_word_count: Optional[int] = None
    num_chapters: int = 25
    tone: str = "narrative"
    style: str = "third person"
    
    # Story elements
    characters: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    world_rules: Dict[str, Any] = field(default_factory=dict)
    timeline: List[Dict[str, Any]] = field(default_factory=list)
    story_arc: Dict[str, str] = field(default_factory=dict)  # beginning, middle, end
    
    # Generated content
    outline: List[Dict[str, Any]] = field(default_factory=list)
    chapters: Dict[int, Dict[str, Any]] = field(default_factory=dict)
    
    def add_character(self, name: str, traits: Dict[str, Any]):
        """Add or update a character."""
        self.characters[name] = traits
    
    def add_world_rule(self, rule: str, description: str):
        """Add a worldbuilding rule."""
        self.world_rules[rule] = description
    
    def add_timeline_event(self, chapter: int, event: str):
        """Add an event to the timeline."""
        self.timeline.append({"chapter": chapter, "event": event})


class ManagerAgent:
    """
    Manager Agent: Plans, supervises, and reviews book generation.
    
    Responsibilities:
    - Interpret user input and define book plan
    - Instruct Writer agent with structured tasks
    - Review Writer outputs for quality and consistency
    - Maintain global state (characters, world, timeline)
    - Approve sections/chapters when ready
    """
    
    def __init__(self, llm_client: LLMClient, book_state: BookState):
        self.llm_client = llm_client
        self.book_state = book_state
        self.revision_count = {}  # Track revisions per section
    
    async def create_book_plan(self) -> Dict[str, Any]:
        """Create the overall book plan from title and premise."""
        system_prompt = """You are a professional book editor and project manager. 
Your role is to analyze a book premise and create a comprehensive plan for the book's structure and story arc."""
        
        user_prompt = f"""Book Title: {self.book_state.title}

Premise: {self.book_state.premise}

Target Word Count: {self.book_state.target_word_count or 'Not specified'}
Number of Chapters: {self.book_state.num_chapters}
Tone: {self.book_state.tone}
Style: {self.book_state.style}

Create a comprehensive book plan that includes:
1. A 2-3 sentence synopsis for the beginning of the story
2. A 2-3 sentence synopsis for the middle of the story
3. A 2-3 sentence synopsis for the end of the story
4. Suggested number of chapters (if not specified, recommend based on premise)
5. Key characters that should be introduced
6. Important worldbuilding elements or rules

Format your response as JSON:
{{
    "story_arc": {{
        "beginning": "...",
        "middle": "...",
        "end": "..."
    }},
    "recommended_chapters": number,
    "key_characters": ["character1", "character2", ...],
    "world_elements": ["element1", "element2", ...]
}}"""
        
        response = await self.llm_client.complete(system=system_prompt, user=user_prompt)
        
        # Try to extract JSON from response
        try:
            # Find JSON in response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                plan = json.loads(response[json_start:json_end])
            else:
                # Fallback: create plan from text
                plan = self._parse_plan_from_text(response)
        except json.JSONDecodeError:
            plan = self._parse_plan_from_text(response)
        
        # Update book state
        if "story_arc" in plan:
            self.book_state.story_arc = plan["story_arc"]
        if "recommended_chapters" in plan:
            self.book_state.num_chapters = plan["recommended_chapters"]
        if "key_characters" in plan:
            for char in plan["key_characters"]:
                self.book_state.add_character(char, {"introduced": False})
        if "world_elements" in plan:
            for elem in plan["world_elements"]:
                self.book_state.add_world_rule(elem, "")
        
        return plan
    
    def _parse_plan_from_text(self, text: str) -> Dict[str, Any]:
        """Fallback parser if JSON extraction fails."""
        plan = {
            "story_arc": {
                "beginning": "The story begins...",
                "middle": "In the middle...",
                "end": "The story concludes..."
            },
            "recommended_chapters": self.book_state.num_chapters,
            "key_characters": [],
            "world_elements": []
        }
        return plan
    
    async def instruct_writer_for_chapter_outline(self, chapter_num: int) -> AgentMessage:
        """Create instruction message for Writer to generate chapter outline."""
        # Get context from previous chapters
        context = self._build_context_summary(chapter_num)
        
        # Determine chapter position in story arc
        total_chapters = self.book_state.num_chapters
        if chapter_num <= total_chapters // 3:
            arc_position = "beginning"
        elif chapter_num <= (total_chapters * 2) // 3:
            arc_position = "middle"
        else:
            arc_position = "end"
        
        story_arc_context = self.book_state.story_arc.get(arc_position, "")
        
        task = f"""Create a detailed outline for Chapter {chapter_num} of "{self.book_state.title}".

The chapter should have:
- A specific, descriptive chapter title (not "Chapter {chapter_num}")
- 2-3 Sections, each with a descriptive title
- Each Section should have 2 Subsections with descriptive titles
- Each Subsection should have 3-5 main points (one per paragraph)

Main points must be FULL SENTENCES (10+ words) describing what happens in that paragraph.
Example: "Introduce Daniel, a tired Earth engineer living in a collapsing megacity, who secretly dreams of the stars."

Story Arc Context ({arc_position}): {story_arc_context}"""
        
        constraints = {
            "chapter_number": chapter_num,
            "sections_count": 2 if chapter_num == 1 else 3,  # First chapter has 2 sections
            "subsections_per_section": 2,
            "main_points_per_subsection": 3,
            "tone": self.book_state.tone,
            "style": self.book_state.style,
            "characters": list(self.book_state.characters.keys()),
            "world_rules": list(self.book_state.world_rules.keys())
        }
        
        expected_format = """JSON format:
{{
    "chapter_title": "Specific descriptive title",
    "sections": [
        {{
            "section_title": "Specific descriptive title",
            "subsections": [
                {{
                    "subsection_title": "Specific descriptive title",
                    "main_points": [
                        "Full sentence describing paragraph 1",
                        "Full sentence describing paragraph 2",
                        "Full sentence describing paragraph 3"
                    ]
                }}
            ]
        }}
    ]
}}"""
        
        return AgentMessage(
            role=MessageRole.MANAGER,
            task=task,
            context_summary=context,
            constraints=constraints,
            expected_output_format=expected_format
        )
    
    async def instruct_writer_for_main_points(self, chapter_num: int, section_num: int, subsection_num: int) -> AgentMessage:
        """Create instruction for Writer to fill in main points for a subsection."""
        chapter = self.book_state.outline[chapter_num - 1] if chapter_num <= len(self.book_state.outline) else None
        section = None
        subsection = None
        
        if chapter:
            sections = chapter.get("sections", [])
            if section_num <= len(sections):
                section = sections[section_num - 1]
                subsections = section.get("subsections", [])
                if subsection_num <= len(subsections):
                    subsection = subsections[subsection_num - 1]
        
        context = self._build_context_summary(chapter_num)
        
        task = f"""Fill in the main points for Chapter {chapter_num}, Section {section_num}, Subsection {subsection_num}.

Chapter: {chapter.get('title', 'N/A') if chapter else 'N/A'}
Section: {section.get('title', 'N/A') if section else 'N/A'}
Subsection: {subsection.get('title', 'N/A') if subsection else 'N/A'}

Generate 3-5 main points. Each main point must be a FULL SENTENCE (10+ words minimum) 
describing what happens in that paragraph. Be specific and story-relevant.

Example format:
- "Introduce Daniel, a tired Earth engineer living in a collapsing megacity, who secretly dreams of the stars."
- "He receives a mysterious encrypted message inviting him to join an advanced Martian civilization that has watched Earth for decades."
- "The message promises clean air, limitless energy, and a new life, but warns that he can never return to Earth."
"""
        
        constraints = {
            "chapter_number": chapter_num,
            "section_number": section_num,
            "subsection_number": subsection_num,
            "main_points_count": 3,
            "min_words_per_point": 10,
            "tone": self.book_state.tone
        }
        
        expected_format = """Array of strings, each a full sentence:
[
    "Full sentence describing paragraph 1",
    "Full sentence describing paragraph 2",
    "Full sentence describing paragraph 3"
]"""
        
        return AgentMessage(
            role=MessageRole.MANAGER,
            task=task,
            context_summary=context,
            constraints=constraints,
            expected_output_format=expected_format
        )
    
    async def review_writer_output(self, message: AgentMessage, output: Any, output_type: str) -> Dict[str, Any]:
        """
        Review Writer's output for quality, consistency, and completeness.
        
        Returns:
            {
                "approved": bool,
                "feedback": str (if not approved),
                "revisions_needed": List[str]
            }
        """
        system_prompt = """You are a professional book editor reviewing content for quality, consistency, and completeness."""
        
        context = f"""Book Title: {self.book_state.title}
Premise: {self.book_state.premise}
Story Arc: {json.dumps(self.book_state.story_arc, indent=2)}
Characters: {json.dumps(self.book_state.characters, indent=2)}
World Rules: {json.dumps(self.book_state.world_rules, indent=2)}"""
        
        if output_type == "chapter_outline":
            review_prompt = f"""Review this chapter outline for Chapter {message.constraints.get('chapter_number', 'N/A')}:

{json.dumps(output, indent=2)}

Check for:
1. Quality: Are titles specific and descriptive (not generic like "Section 1")?
2. Completeness: Does it have the required structure (sections, subsections, main points)?
3. Consistency: Does it align with the premise and story arc?
4. Detail: Are main points full sentences (10+ words) with specific content?

Respond with JSON:
{{
    "approved": true/false,
    "feedback": "Detailed feedback",
    "revisions_needed": ["item1", "item2", ...]
}}"""
        else:  # main_points
            review_prompt = f"""Review these main points:

{json.dumps(output, indent=2)}

Check for:
1. Each point is a full sentence (10+ words)
2. Points are specific and story-relevant
3. Points follow logical progression
4. No placeholder text like "Main point for paragraph 1"

Respond with JSON:
{{
    "approved": true/false,
    "feedback": "Detailed feedback",
    "revisions_needed": ["item1", "item2", ...]
}}"""
        
        user_prompt = f"""{context}

{review_prompt}"""
        
        response = await self.llm_client.complete(system=system_prompt, user=user_prompt)
        
        # Extract JSON from response
        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                review = json.loads(response[json_start:json_end])
            else:
                # Default: approve if we can't parse
                review = {"approved": True, "feedback": "Unable to parse review, approving by default", "revisions_needed": []}
        except json.JSONDecodeError:
            review = {"approved": True, "feedback": "JSON parse error, approving by default", "revisions_needed": []}
        
        return review
    
    def _build_context_summary(self, current_chapter: int) -> str:
        """Build a context summary for the Writer agent."""
        summary_parts = [
            f"Book: {self.book_state.title}",
            f"Premise: {self.book_state.premise}",
            f"Current Chapter: {current_chapter} of {self.book_state.num_chapters}",
        ]
        
        if self.book_state.story_arc:
            summary_parts.append(f"Story Arc: {json.dumps(self.book_state.story_arc)}")
        
        if self.book_state.characters:
            summary_parts.append(f"Characters: {', '.join(self.book_state.characters.keys())}")
        
        # Add previous chapter summaries
        if current_chapter > 1 and current_chapter - 1 <= len(self.book_state.outline):
            prev_chapter = self.book_state.outline[current_chapter - 2]
            summary_parts.append(f"Previous Chapter: {prev_chapter.get('title', 'N/A')}")
        
        return "\n".join(summary_parts)
    
    def approve_chapter(self, chapter_num: int):
        """Mark a chapter as approved and ready for final output."""
        if chapter_num <= len(self.book_state.outline):
            chapter = self.book_state.outline[chapter_num - 1]
            chapter["approved"] = True
            chapter["status"] = "approved"


class WriterAgent:
    """
    Writer Agent: Generates book content based on Manager's instructions.
    
    Responsibilities:
    - Generate detailed chapter outlines
    - Fill in section, subsection, and main-point descriptions
    - Generate full narrative text (optional)
    - Follow style and content instructions
    - Respect continuity constraints
    """
    
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
    
    async def generate_chapter_outline(self, message: AgentMessage) -> Dict[str, Any]:
        """Generate a chapter outline based on Manager's instructions."""
        system_prompt = """You are a professional novelist creating detailed chapter outlines.
Follow the instructions precisely and generate content that matches the specified format and level of detail."""
        
        user_prompt = f"""{message.context_summary}

{message.task}

Constraints:
{json.dumps(message.constraints, indent=2)}

Expected Format:
{message.expected_output_format}

Generate the chapter outline now. Make sure:
- All titles are specific and descriptive (not generic labels)
- All main points are full sentences (10+ words)
- Content is story-specific and relevant to the premise"""
        
        response = await self.llm_client.complete(system=system_prompt, user=user_prompt)
        
        # Try to extract JSON from response
        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                outline = json.loads(response[json_start:json_end])
            else:
                # Fallback: parse from text
                outline = self._parse_outline_from_text(response, message.constraints)
        except json.JSONDecodeError:
            outline = self._parse_outline_from_text(response, message.constraints)
        
        return outline
    
    async def generate_main_points(self, message: AgentMessage) -> List[str]:
        """Generate main points for a subsection."""
        system_prompt = """You are a professional novelist creating detailed paragraph descriptions.
Each main point must be a full sentence (10+ words) describing what happens in that paragraph."""
        
        user_prompt = f"""{message.context_summary}

{message.task}

Constraints:
{json.dumps(message.constraints, indent=2)}

Expected Format:
{message.expected_output_format}

Generate the main points now. Each must be a full sentence with specific story content."""
        
        response = await self.llm_client.complete(system=system_prompt, user=user_prompt)
        
        # Try to extract array from response
        try:
            # Try JSON array first
            json_start = response.find('[')
            json_end = response.rfind(']') + 1
            if json_start >= 0 and json_end > json_start:
                main_points = json.loads(response[json_start:json_end])
            else:
                # Parse from bullet points or numbered list
                main_points = self._parse_main_points_from_text(response)
        except json.JSONDecodeError:
            main_points = self._parse_main_points_from_text(response)
        
        # Ensure all are strings and full sentences
        main_points = [str(mp).strip() for mp in main_points if str(mp).strip()]
        # Filter out placeholders
        main_points = [mp for mp in main_points if len(mp) > 10 and not mp.lower().startswith("main point for paragraph")]
        
        return main_points
    
    async def generate_prose(self, chapter_num: int, section_num: int, subsection_num: int, 
                           main_points: List[str], context: str) -> str:
        """Generate full narrative prose for a subsection (optional feature)."""
        system_prompt = """You are a professional novelist. Write engaging narrative prose that follows the provided outline."""
        
        user_prompt = f"""Write full narrative prose for:
Chapter {chapter_num}, Section {section_num}, Subsection {subsection_num}

Context: {context}

Main Points to cover:
{chr(10).join(f"- {mp}" for mp in main_points)}

Write engaging prose that covers all main points in order. Use the specified tone and style."""
        
        response = await self.llm_client.complete(system=system_prompt, user=user_prompt)
        return response
    
    def _parse_outline_from_text(self, text: str, constraints: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback parser for outline if JSON extraction fails."""
        # Create a basic structure
        outline = {
            "chapter_title": f"Chapter {constraints.get('chapter_number', 1)}",
            "sections": []
        }
        
        sections_count = constraints.get("sections_count", 3)
        subsections_per_section = constraints.get("subsections_per_section", 2)
        main_points_per_subsection = constraints.get("main_points_per_subsection", 3)
        
        for sec_idx in range(sections_count):
            section = {
                "section_title": f"Section {sec_idx + 1}",
                "subsections": []
            }
            for sub_idx in range(subsections_per_section):
                subsection = {
                    "subsection_title": f"Subsection {sec_idx + 1}.{sub_idx + 1}",
                    "main_points": [f"Main point {sub_idx + 1}.{mp_idx + 1}" for mp_idx in range(main_points_per_subsection)]
                }
                section["subsections"].append(subsection)
            outline["sections"].append(section)
        
        return outline
    
    def _parse_main_points_from_text(self, text: str) -> List[str]:
        """Parse main points from text response."""
        main_points = []
        for line in text.split('\n'):
            line = line.strip()
            if not line:
                continue
            # Remove bullet points, numbering, etc.
            line = line.lstrip('*-1234567890. ').strip()
            # Handle "Main point for paragraph X: [sentence]" format
            if ':' in line and 'main point' in line.lower():
                line = line.split(':', 1)[1].strip()
            if line and len(line) > 10:
                main_points.append(line)
        return main_points if main_points else ["Main point placeholder"] * 3


class MultiAgentBookGenerator:
    """
    Main orchestrator for the multi-agent book generation system.
    
    Coordinates the workflow between Manager and Writer agents.
    """
    
    def __init__(self, title: str, premise: str, target_word_count: Optional[int] = None, 
                 num_chapters: int = 25, tone: str = "narrative", style: str = "third person",
                 mid_phase_callback: Optional[callable] = None):
        """Initialize the book generation system."""
        agent_config = get_config()
        
        # Create LLM client
        self.llm_client = LLMClient(
            api_key=None,
            base_url=agent_config.get("base_url", "http://localhost:11434/v1"),
            model=agent_config.get("model", "qwen3:30b"),
            provider=agent_config.get("provider", "local")
        )
        
        # Create book state
        self.book_state = BookState(
            title=title,
            premise=premise,
            target_word_count=target_word_count,
            num_chapters=num_chapters,
            tone=tone,
            style=style
        )
        
        # Create agents
        self.manager = ManagerAgent(self.llm_client, self.book_state)
        self.writer = WriterAgent(self.llm_client)
        
        # Store callback for mid-phase progress saving
        self.mid_phase_callback = mid_phase_callback
    
    async def generate_book(self, generate_prose: bool = False) -> Dict[str, Any]:
        """
        Main workflow for book generation.
        
        Steps:
        1. Input phase - already done (title, premise)
        2. Manager creates book plan
        3. Outline generation phase
        4. Main-point filling phase
        5. (Optional) Prose drafting phase
        6. Final assembly
        """
        print(f"\n{'='*60}")
        print(f"Starting Book Generation: {self.book_state.title}")
        print(f"{'='*60}\n")
        
        # Step 1: Manager creates book plan
        print("Step 1: Manager creating book plan...")
        plan = await self.manager.create_book_plan()
        print(f"✓ Book plan created: {self.book_state.num_chapters} chapters")
        print(f"  Story Arc: {self.book_state.story_arc.get('beginning', 'N/A')[:100]}...\n")
        
        # Step 2: Outline generation phase
        print("Step 2: Generating chapter outlines...")
        for chapter_num in range(1, self.book_state.num_chapters + 1):
            print(f"\n  Chapter {chapter_num}/{self.book_state.num_chapters}...")
            
            max_revisions = 3
            revision_count = 0
            approved = False
            
            while not approved and revision_count < max_revisions:
                # Manager instructs Writer
                message = await self.manager.instruct_writer_for_chapter_outline(chapter_num)
                
                # Writer generates outline
                outline = await self.writer.generate_chapter_outline(message)
                
                # Manager reviews
                review = await self.manager.review_writer_output(message, outline, "chapter_outline")
                
                if review.get("approved", False):
                    # Add to book state
                    chapter_data = {
                        "chapter_number": chapter_num,
                        "title": outline.get("chapter_title", f"Chapter {chapter_num}"),
                        "sections": []
                    }
                    
                    for sec_idx, section_data in enumerate(outline.get("sections", []), 1):
                        section = {
                            "title": section_data.get("section_title", f"Section {sec_idx}"),
                            "subsections": []
                        }
                        
                        for sub_idx, subsection_data in enumerate(section_data.get("subsections", []), 1):
                            subsection = {
                                "title": subsection_data.get("subsection_title", f"Subsection {sec_idx}.{sub_idx}"),
                                "main_points": subsection_data.get("main_points", [])
                            }
                            section["subsections"].append(subsection)
                        
                        chapter_data["sections"].append(section)
                    
                    self.book_state.outline.append(chapter_data)
                    print(f"    ✓ Chapter {chapter_num} outline approved")
                    approved = True
                    
                    # Save progress after each chapter is approved
                    if self.mid_phase_callback:
                        await self.mid_phase_callback(
                            f"Chapter {chapter_num} outline approved",
                            f"Chapter {chapter_num} of {self.book_state.num_chapters}"
                        )
                else:
                    revision_count += 1
                    print(f"    ⚠ Revision {revision_count} needed: {review.get('feedback', 'N/A')[:100]}")
                    # Add feedback to message for next iteration
                    message.feedback = review.get("feedback", "")
            
            if not approved:
                print(f"    ✗ Chapter {chapter_num} failed after {max_revisions} revisions")
        
        # Step 3: Main-point filling phase (ensure all main points are filled)
        print(f"\nStep 3: Filling in main points...")
        for chapter_idx, chapter in enumerate(self.book_state.outline, 1):
            for section_idx, section in enumerate(chapter.get("sections", []), 1):
                for subsection_idx, subsection in enumerate(section.get("subsections", []), 1):
                    main_points = subsection.get("main_points", [])
                    
                    # Check if main points need to be filled or improved
                    needs_filling = False
                    for mp in main_points:
                        mp_text = str(mp) if isinstance(mp, str) else mp.get("text", "")
                        if len(mp_text) < 10 or "main point" in mp_text.lower() and len(mp_text) < 30:
                            needs_filling = True
                            break
                    
                    if needs_filling or not main_points:
                        print(f"  Filling main points for Chapter {chapter_idx}, Section {section_idx}, Subsection {subsection_idx}...")
                        
                        message = await self.manager.instruct_writer_for_main_points(
                            chapter_idx, section_idx, subsection_idx
                        )
                        
                        new_main_points = await self.writer.generate_main_points(message)
                        
                        # Review main points
                        review = await self.manager.review_writer_output(message, new_main_points, "main_points")
                        
                        if review.get("approved", False) and new_main_points:
                            # Update main points
                            subsection["main_points"] = [{"text": mp} if isinstance(mp, str) else mp for mp in new_main_points]
                            print(f"    ✓ Main points approved")
                        else:
                            print(f"    ⚠ Main points need improvement: {review.get('feedback', 'N/A')[:100]}")
        
        # Step 4: (Optional) Prose generation
        if generate_prose:
            print(f"\nStep 4: Generating prose...")
            for chapter_idx, chapter in enumerate(self.book_state.outline, 1):
                chapter["prose"] = {}
                for section_idx, section in enumerate(chapter.get("sections", []), 1):
                    chapter["prose"][section_idx] = {}
                    for subsection_idx, subsection in enumerate(section.get("subsections", []), 1):
                        main_points = [mp.get("text") if isinstance(mp, dict) else str(mp) for mp in subsection.get("main_points", [])]
                        context = self.manager._build_context_summary(chapter_idx)
                        
                        prose = await self.writer.generate_prose(
                            chapter_idx, section_idx, subsection_idx, main_points, context
                        )
                        chapter["prose"][section_idx][subsection_idx] = prose
                        print(f"  ✓ Generated prose for Chapter {chapter_idx}, Section {section_idx}, Subsection {subsection_idx}")
        
        # Step 5: Final assembly
        print(f"\nStep 5: Final assembly...")
        result = self._assemble_final_output()
        print(f"✓ Book generation complete!\n")
        
        return result
    
    def _assemble_final_output(self) -> Dict[str, Any]:
        """Assemble the final book output."""
        return {
            "title": self.book_state.title,
            "premise": self.book_state.premise,
            "story_arc": self.book_state.story_arc,
            "characters": self.book_state.characters,
            "world_rules": self.book_state.world_rules,
            "outline": self.book_state.outline,
            "total_chapters": len(self.book_state.outline)
        }
    
    def export_to_markdown(self, output_path: str, include_prose: bool = False):
        """Export the book to a markdown file."""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"# {self.book_state.title}\n\n")
            f.write(f"**Premise:** {self.book_state.premise}\n\n")
            
            for chapter in self.book_state.outline:
                f.write(f"## Chapter {chapter['chapter_number']} – {chapter['title']}\n\n")
                
                for section in chapter.get("sections", []):
                    f.write(f"### Section {chapter['chapter_number']}.{chapter['sections'].index(section) + 1} – {section['title']}\n\n")
                    
                    for subsection in section.get("subsections", []):
                        sub_num = section['subsections'].index(subsection) + 1
                        sec_num = chapter['sections'].index(section) + 1
                        f.write(f"#### Subsection {sec_num}.{sub_num} – {subsection['title']}\n\n")
                        
                        # Main points
                        for mp_idx, mp in enumerate(subsection.get("main_points", []), 1):
                            mp_text = mp.get("text") if isinstance(mp, dict) else str(mp)
                            f.write(f"- {mp_text}\n")
                        f.write("\n")
                        
                        # Prose (if available)
                        if include_prose and "prose" in chapter:
                            prose = chapter["prose"].get(sec_num, {}).get(sub_num, "")
                            if prose:
                                f.write(f"{prose}\n\n")
        
        print(f"✓ Exported to {output_path}")


# Example usage and CLI entry point
async def main():
    """
    CLI entry point for the multi-agent book generation system.
    
    Example usage:
        python -m app.book_writer.multi_agent_system
    """
    print("=" * 60)
    print("Multi-Agent Book Generation System")
    print("=" * 60)
    print()
    
    # Get user input
    title = input("Enter book title: ").strip()
    premise = input("Enter premise (1-3 sentences): ").strip()
    
    num_chapters_input = input("Enter number of chapters (default 25): ").strip()
    num_chapters = int(num_chapters_input) if num_chapters_input else 25
    
    tone = input("Enter tone (default: narrative): ").strip() or "narrative"
    style = input("Enter style (default: third person): ").strip() or "third person"
    
    generate_prose_input = input("Generate full prose? (y/n, default: n): ").strip().lower()
    generate_prose = generate_prose_input == 'y'
    
    # Create generator
    generator = MultiAgentBookGenerator(
        title=title,
        premise=premise,
        num_chapters=num_chapters,
        tone=tone,
        style=style
    )
    
    # Generate book
    result = await generator.generate_book(generate_prose=generate_prose)
    
    # Export
    output_path = f"{title.replace(' ', '_')}_outline.md"
    generator.export_to_markdown(output_path, include_prose=generate_prose)
    
    print(f"\n✓ Book generation complete!")
    print(f"  Outline saved to: {output_path}")
    print(f"  Total chapters: {result['total_chapters']}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

