"""
Ferrari-Style Multi-Agent Book Creation Company

This module implements a complete organizational structure where every role is an AI agent,
mirroring Ferrari's car production pipeline but for book creation.

The Owner (human user) has absolute override and can see all agent communications.
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import json
import asyncio
from app.llm.client import LLMClient
from app.book_writer.config import get_config


class Phase(Enum):
    """Book creation phases mirroring Ferrari pipeline."""
    STRATEGY_CONCEPT = "strategy_concept"
    EARLY_DESIGN = "early_design"
    DETAILED_ENGINEERING = "detailed_engineering"
    PROTOTYPES_TESTING = "prototypes_testing"
    INDUSTRIALIZATION_PACKAGING = "industrialization_packaging"
    MARKETING_LAUNCH = "marketing_launch"
    COMPLETE = "complete"


class OwnerDecision(Enum):
    """Owner's decision on phase approval."""
    APPROVE = "approve"
    REQUEST_CHANGES = "request_changes"
    STOP = "stop"


@dataclass
class AgentMessage:
    """Message in the company chat log."""
    from_agent: str
    to_agent: str
    phase: Phase
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    message_type: str = "internal"  # internal, owner_request, owner_response
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "from_agent": self.from_agent,
            "to_agent": self.to_agent,
            "phase": self.phase.value,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "message_type": self.message_type
        }


@dataclass
class BookProject:
    """Complete book project state."""
    title: Optional[str] = None
    premise: str = ""
    target_word_count: Optional[int] = None
    audience: Optional[str] = None
    genre: Optional[str] = None
    
    # Phase outputs
    book_brief: Optional[Dict[str, Any]] = None
    world_dossier: Optional[Dict[str, Any]] = None
    character_bible: Optional[Dict[str, Any]] = None
    plot_arc: Optional[Dict[str, Any]] = None
    outline: Optional[List[Dict[str, Any]]] = None
    draft_chapters: Dict[int, str] = field(default_factory=dict)
    full_draft: Optional[str] = None
    revision_report: Optional[Dict[str, Any]] = None
    formatted_manuscript: Optional[str] = None
    launch_package: Optional[Dict[str, Any]] = None
    
    # Metadata
    current_phase: Phase = Phase.STRATEGY_CONCEPT
    status: str = "in_progress"
    owner_edits: Dict[str, Any] = field(default_factory=dict)


class MessageBus:
    """Central message bus for all agent communications."""
    
    def __init__(self):
        self.messages: List[AgentMessage] = []
        self.subscribers: Dict[str, List[callable]] = {}
    
    def send(self, from_agent: str, to_agent: str, phase: Phase, content: str, 
             message_type: str = "internal"):
        """Send a message and log it."""
        message = AgentMessage(
            from_agent=from_agent,
            to_agent=to_agent,
            phase=phase,
            content=content,
            message_type=message_type
        )
        self.messages.append(message)
        
        # Notify subscribers
        if to_agent in self.subscribers:
            for callback in self.subscribers[to_agent]:
                callback(message)
        
        return message
    
    def get_chat_log(self, phase: Optional[Phase] = None) -> List[Dict[str, Any]]:
        """Get full chat log, optionally filtered by phase."""
        messages = self.messages
        if phase:
            messages = [m for m in messages if m.phase == phase]
        return [m.to_dict() for m in messages]
    
    def subscribe(self, agent_name: str, callback: callable):
        """Subscribe an agent to receive messages."""
        if agent_name not in self.subscribers:
            self.subscribers[agent_name] = []
        self.subscribers[agent_name].append(callback)


class BaseAgent:
    """Base class for all company agents."""
    
    def __init__(self, name: str, role: str, llm_client: LLMClient, message_bus: MessageBus):
        self.name = name
        self.role = role
        self.llm_client = llm_client
        self.message_bus = message_bus
    
    async def send_message(self, to_agent: str, phase: Phase, content: str):
        """Send a message via the message bus."""
        return self.message_bus.send(self.name, to_agent, phase, content)
    
    async def receive_message(self, message: AgentMessage):
        """Handle received message (override in subclasses)."""
        pass
    
    async def execute_task(self, task: str, context: Dict[str, Any]) -> Any:
        """Execute a task using LLM (override in subclasses)."""
        pass


class CEOAgent(BaseAgent):
    """CEO Agent - Overall coordination and Owner communication."""
    
    def __init__(self, llm_client: LLMClient, message_bus: MessageBus):
        super().__init__("CEO", "Chief Executive Officer", llm_client, message_bus)
        self.project: Optional[BookProject] = None
    
    async def present_to_owner(self, phase: Phase, summary: str, artifacts: Dict[str, Any]) -> OwnerDecision:
        """Present phase results to Owner and get decision."""
        presentation = f"""
=== PHASE COMPLETE: {phase.value.upper().replace('_', ' ')} ===

Summary:
{summary}

Key Artifacts:
{json.dumps(artifacts, indent=2)}

---
CEO Question: Approve, request changes, or stop the project?
"""
        
        # Log owner request
        self.message_bus.send(
            "CEO",
            "Owner",
            phase,
            presentation,
            message_type="owner_request"
        )
        
        # Check if owner callback is set (by company)
        if hasattr(self, '_owner_callback') and self._owner_callback:
            # Call the owner callback (which is a regular function, not async)
            callback_result = self._owner_callback(phase, summary, artifacts)
            # The callback returns OwnerDecision directly (synchronous)
            return callback_result
        
        # Default: approve (for testing/automation)
        return OwnerDecision.APPROVE
    
    async def coordinate_phase(self, phase: Phase, project: BookProject) -> Tuple[Dict[str, Any], OwnerDecision]:
        """Coordinate a phase and get Owner approval."""
        self.project = project
        
        if phase == Phase.STRATEGY_CONCEPT:
            return await self._strategy_concept_phase()
        elif phase == Phase.EARLY_DESIGN:
            return await self._early_design_phase()
        elif phase == Phase.DETAILED_ENGINEERING:
            return await self._detailed_engineering_phase()
        elif phase == Phase.PROTOTYPES_TESTING:
            return await self._prototypes_testing_phase()
        elif phase == Phase.INDUSTRIALIZATION_PACKAGING:
            return await self._industrialization_packaging_phase()
        elif phase == Phase.MARKETING_LAUNCH:
            return await self._marketing_launch_phase()
        else:
            return {}, OwnerDecision.STOP
    
    async def _strategy_concept_phase(self) -> Tuple[Dict[str, Any], OwnerDecision]:
        """Phase 1: Strategy & Concept."""
        await self.send_message("CPSO", Phase.STRATEGY_CONCEPT, 
                              f"Create book brief for: {self.project.premise}")
        
        # CPSO will create brief (handled by company orchestrator)
        # This is a placeholder - actual work done by CPSO agent
        
        summary = "CPSO has created the initial book brief."
        artifacts = {"book_brief": self.project.book_brief or {}}
        
        decision = await self.present_to_owner(Phase.STRATEGY_CONCEPT, summary, artifacts)
        return artifacts, decision
    
    async def _early_design_phase(self) -> Tuple[Dict[str, Any], OwnerDecision]:
        """Phase 2: Early Design."""
        summary = "Story Design Director has completed world and character design."
        artifacts = {
            "world_dossier": self.project.world_dossier or {},
            "character_bible": self.project.character_bible or {},
            "plot_arc": self.project.plot_arc or {}
        }
        decision = await self.present_to_owner(Phase.EARLY_DESIGN, summary, artifacts)
        return artifacts, decision
    
    async def _detailed_engineering_phase(self) -> Tuple[Dict[str, Any], OwnerDecision]:
        """Phase 3: Detailed Engineering."""
        summary = "Narrative Engineering Director has created the full hierarchical outline."
        artifacts = {"outline": self.project.outline or []}
        decision = await self.present_to_owner(Phase.DETAILED_ENGINEERING, summary, artifacts)
        return artifacts, decision
    
    async def _prototypes_testing_phase(self) -> Tuple[Dict[str, Any], OwnerDecision]:
        """Phase 4: Prototypes & Testing."""
        summary = "Production and QA teams have completed draft and testing."
        artifacts = {
            "draft_chapters": self.project.draft_chapters,
            "revision_report": self.project.revision_report or {}
        }
        decision = await self.present_to_owner(Phase.PROTOTYPES_TESTING, summary, artifacts)
        return artifacts, decision
    
    async def _industrialization_packaging_phase(self) -> Tuple[Dict[str, Any], OwnerDecision]:
        """Phase 5: Industrialization & Packaging."""
        summary = "Formatting and export agents have prepared the production-ready manuscript."
        artifacts = {"formatted_manuscript": self.project.formatted_manuscript or ""}
        decision = await self.present_to_owner(Phase.INDUSTRIALIZATION_PACKAGING, summary, artifacts)
        return artifacts, decision
    
    async def _marketing_launch_phase(self) -> Tuple[Dict[str, Any], OwnerDecision]:
        """Phase 6: Marketing & Launch."""
        summary = "Launch Director has created the complete launch package."
        artifacts = {"launch_package": self.project.launch_package or {}}
        decision = await self.present_to_owner(Phase.MARKETING_LAUNCH, summary, artifacts)
        return artifacts, decision


class CPSOAgent(BaseAgent):
    """Chief Product/Story Officer - Creates book brief."""
    
    def __init__(self, llm_client: LLMClient, message_bus: MessageBus):
        super().__init__("CPSO", "Chief Product/Story Officer", llm_client, message_bus)
    
    async def create_book_brief(self, premise: str, title: Optional[str], 
                               target_word_count: Optional[int], audience: Optional[str]) -> Dict[str, Any]:
        """Create the book brief."""
        system_prompt = """You are the Chief Product/Story Officer. Your role is to analyze a book idea and create a comprehensive book brief that defines the product strategy."""
        
        user_prompt = f"""Create a comprehensive book brief for:

Title: {title or 'TBD'}
Premise: {premise}
Target Word Count: {target_word_count or 'Not specified'}
Target Audience: {audience or 'Not specified'}

The brief must include:
1. Genre classification
2. Target audience (if not specified, recommend based on premise)
3. Recommended word count (if not specified, recommend based on genre)
4. Core themes
5. Tone and style recommendations
6. Key constraints or requirements
7. Success criteria

Format as JSON:
{{
    "genre": "...",
    "target_audience": "...",
    "recommended_word_count": number,
    "core_themes": ["theme1", "theme2", ...],
    "tone": "...",
    "style": "...",
    "constraints": ["constraint1", ...],
    "success_criteria": ["criterion1", ...]
}}"""
        
        response = await self.llm_client.complete(system=system_prompt, user=user_prompt)
        
        # Extract JSON
        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                brief = json.loads(response[json_start:json_end])
            else:
                brief = self._parse_brief_from_text(response)
        except json.JSONDecodeError:
            brief = self._parse_brief_from_text(response)
        
        await self.send_message("CEO", Phase.STRATEGY_CONCEPT, 
                              f"Book brief created: {json.dumps(brief, indent=2)}")
        
        return brief
    
    def _parse_brief_from_text(self, text: str) -> Dict[str, Any]:
        """Fallback parser for brief."""
        return {
            "genre": "Fiction",
            "target_audience": "General",
            "recommended_word_count": 80000,
            "core_themes": [],
            "tone": "narrative",
            "style": "third person",
            "constraints": [],
            "success_criteria": []
        }


class StoryDesignDirectorAgent(BaseAgent):
    """Story Design Director - Coordinates design workshop."""
    
    def __init__(self, llm_client: LLMClient, message_bus: MessageBus):
        super().__init__("StoryDesignDirector", "Story Design Director", llm_client, message_bus)
        self.worldbuilding_designers = []
        self.character_designers = []
        self.tone_mood_agents = []
    
    async def run_design_workshop(self, book_brief: Dict[str, Any], premise: str) -> Dict[str, Any]:
        """Run the design workshop with all design agents."""
        # Coordinate worldbuilding
        world_dossier = await self._create_world_dossier(book_brief, premise)
        
        # Coordinate character design
        character_bible = await self._create_character_bible(book_brief, premise)
        
        # Coordinate tone & mood
        tone_mood = await self._create_tone_mood_guide(book_brief, premise)
        
        # Create plot arc
        plot_arc = await self._create_plot_arc(book_brief, premise, world_dossier, character_bible)
        
        result = {
            "world_dossier": world_dossier,
            "character_bible": character_bible,
            "tone_mood": tone_mood,
            "plot_arc": plot_arc
        }
        
        await self.send_message("CEO", Phase.EARLY_DESIGN, 
                              f"Design workshop complete. Created world, characters, and plot arc.")
        
        return result
    
    async def _create_world_dossier(self, brief: Dict[str, Any], premise: str) -> Dict[str, Any]:
        """Worldbuilding Designer Agent work."""
        system_prompt = """You are a Worldbuilding Designer Agent. Create detailed world documentation."""
        
        user_prompt = f"""Create a comprehensive world dossier for:

Premise: {premise}
Genre: {brief.get('genre', 'Fiction')}
Themes: {brief.get('core_themes', [])}

Include:
1. World/setting description
2. Rules and laws (physical, magical, social)
3. Key locations
4. Technology level (if applicable)
5. Culture and society
6. History and timeline
7. Unique elements

Format as JSON."""
        
        response = await self.llm_client.complete(system=system_prompt, user=user_prompt)
        
        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                return json.loads(response[json_start:json_end])
        except:
            pass
        
        return {"description": response[:500], "rules": [], "locations": []}
    
    async def _create_character_bible(self, brief: Dict[str, Any], premise: str) -> Dict[str, Any]:
        """Character Designer Agent work."""
        system_prompt = """You are a Character Designer Agent. Create detailed character documentation."""
        
        user_prompt = f"""Create a character bible for:

Premise: {premise}
Genre: {brief.get('genre', 'Fiction')}

Include:
1. Main characters with detailed profiles
2. Supporting characters
3. Character arcs and development
4. Relationships
5. Motivations and goals
6. Physical descriptions
7. Personality traits

Format as JSON."""
        
        response = await self.llm_client.complete(system=system_prompt, user=user_prompt)
        
        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                return json.loads(response[json_start:json_end])
        except:
            pass
        
        return {"main_characters": [], "supporting_characters": []}
    
    async def _create_tone_mood_guide(self, brief: Dict[str, Any], premise: str) -> Dict[str, Any]:
        """Tone & Mood Agent work."""
        system_prompt = """You are a Tone & Mood Agent. Define the emotional and stylistic tone."""
        
        user_prompt = f"""Create a tone and mood guide for:

Premise: {premise}
Genre: {brief.get('genre', 'Fiction')}
Recommended Tone: {brief.get('tone', 'narrative')}

Define:
1. Overall tone
2. Mood variations by section
3. Emotional arc
4. Writing style guidelines
5. Pacing recommendations

Format as JSON."""
        
        response = await self.llm_client.complete(system=system_prompt, user=user_prompt)
        
        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                return json.loads(response[json_start:json_end])
        except:
            pass
        
        return {"overall_tone": brief.get('tone', 'narrative'), "mood_variations": []}
    
    async def _create_plot_arc(self, brief: Dict[str, Any], premise: str, 
                              world_dossier: Dict[str, Any], character_bible: Dict[str, Any]) -> Dict[str, Any]:
        """Create high-level plot arc."""
        system_prompt = """You are a Plot Architect. Create the high-level story arc."""
        
        user_prompt = f"""Create a high-level plot arc for:

Premise: {premise}
Genre: {brief.get('genre', 'Fiction')}
World: {json.dumps(world_dossier, indent=2)[:500]}
Characters: {json.dumps(character_bible, indent=2)[:500]}

Define:
1. Three-act structure (beginning, middle, end)
2. Key plot points
3. Major turning points
4. Climax
5. Resolution

Format as JSON."""
        
        response = await self.llm_client.complete(system=system_prompt, user=user_prompt)
        
        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                return json.loads(response[json_start:json_end])
        except:
            pass
        
        return {"beginning": "", "middle": "", "end": ""}


class NarrativeEngineeringDirectorAgent(BaseAgent):
    """Narrative Engineering Director - Creates full hierarchical outline."""
    
    def __init__(self, llm_client: LLMClient, message_bus: MessageBus):
        super().__init__("NarrativeEngineeringDirector", "Narrative Engineering Director", 
                        llm_client, message_bus)
    
    async def create_outline(self, project: BookProject) -> List[Dict[str, Any]]:
        """Create full hierarchical outline using engineering team."""
        # Use the existing multi-agent system for outline generation
        from app.book_writer.multi_agent_system import MultiAgentBookGenerator
        
        generator = MultiAgentBookGenerator(
            title=project.title or "Untitled",
            premise=project.premise,
            target_word_count=project.target_word_count,
            num_chapters=project.book_brief.get('recommended_word_count', 80000) // 3000 if project.book_brief else 25,
            tone=project.book_brief.get('tone', 'narrative') if project.book_brief else 'narrative',
            style=project.book_brief.get('style', 'third person') if project.book_brief else 'third person'
        )
        
        # Generate outline
        result = await generator.generate_book(generate_prose=False)
        outline = result.get('outline', [])
        
        await self.send_message("CEO", Phase.DETAILED_ENGINEERING, 
                              f"Full hierarchical outline created with {len(outline)} chapters.")
        
        return outline


class ProductionDirectorAgent(BaseAgent):
    """Production Director - Coordinates drafting and assembly."""
    
    def __init__(self, llm_client: LLMClient, message_bus: MessageBus):
        super().__init__("ProductionDirector", "Production Director", llm_client, message_bus)
        self.drafting_agents = []
        self.assembly_agents = []
    
    async def create_draft(self, project: BookProject) -> Dict[int, str]:
        """Create full draft using drafting agents."""
        draft_chapters = {}
        
        if not project.outline:
            return draft_chapters
        
        for chapter_data in project.outline:
            chapter_num = chapter_data.get('chapter_number', 0)
            
            # Drafting agent writes chapter
            chapter_text = await self._draft_chapter(chapter_data, project)
            draft_chapters[chapter_num] = chapter_text
            
            await self.send_message("CEO", Phase.PROTOTYPES_TESTING, 
                                  f"Drafted Chapter {chapter_num}")
        
        # Assembly agent combines chapters
        full_draft = await self._assemble_draft(draft_chapters)
        project.full_draft = full_draft
        
        await self.send_message("CEO", Phase.PROTOTYPES_TESTING, 
                              f"Full draft assembled: {len(full_draft)} characters")
        
        return draft_chapters
    
    async def _draft_chapter(self, chapter_data: Dict[str, Any], project: BookProject) -> str:
        """Drafting Agent writes a chapter."""
        system_prompt = """You are a Drafting Agent. Write engaging narrative prose following the provided outline."""
        
        context = f"""Book: {project.title}
Premise: {project.premise}
World: {json.dumps(project.world_dossier, indent=2)[:500] if project.world_dossier else 'N/A'}
Characters: {json.dumps(project.character_bible, indent=2)[:500] if project.character_bible else 'N/A'}"""
        
        outline_text = json.dumps(chapter_data, indent=2)
        
        user_prompt = f"""Write Chapter {chapter_data.get('chapter_number', 1)}: {chapter_data.get('title', 'Untitled')}

{context}

Chapter Outline:
{outline_text}

Write full narrative prose that follows the outline structure. Each subsection should be expanded into engaging prose."""
        
        response = await self.llm_client.complete(system=system_prompt, user=user_prompt)
        return response
    
    async def _assemble_draft(self, draft_chapters: Dict[int, str]) -> str:
        """Assembly Agent combines chapters into full draft."""
        chapters = [draft_chapters[i] for i in sorted(draft_chapters.keys())]
        return "\n\n".join([f"# Chapter {i+1}\n\n{ch}" for i, ch in enumerate(chapters)])


class QADirectorAgent(BaseAgent):
    """QA Director - Coordinates testing and quality assurance."""
    
    def __init__(self, llm_client: LLMClient, message_bus: MessageBus):
        super().__init__("QADirector", "QA Director", llm_client, message_bus)
        self.test_readers = []
        self.logic_consistency_agents = []
        self.sensitivity_agents = []
    
    async def test_and_review(self, project: BookProject) -> Dict[str, Any]:
        """Run full QA testing."""
        revision_report = {
            "test_reader_feedback": await self._test_reader_evaluation(project),
            "logic_consistency_issues": await self._logic_consistency_check(project),
            "sensitivity_issues": await self._sensitivity_review(project),
            "overall_assessment": "",
            "recommended_changes": []
        }
        
        # Create overall assessment
        revision_report["overall_assessment"] = await self._create_assessment(revision_report)
        revision_report["recommended_changes"] = await self._identify_changes(revision_report)
        
        await self.send_message("CEO", Phase.PROTOTYPES_TESTING, 
                              f"QA testing complete. Found {len(revision_report['recommended_changes'])} recommended changes.")
        
        return revision_report
    
    async def _test_reader_evaluation(self, project: BookProject) -> Dict[str, Any]:
        """Test Reader Agent evaluation."""
        system_prompt = """You are a Test Reader Agent. Evaluate pacing, emotional impact, and reader engagement."""
        
        draft_sample = project.full_draft[:2000] if project.full_draft else "No draft available"
        
        user_prompt = f"""Evaluate this book draft:

Title: {project.title}
Premise: {project.premise}

Draft Sample:
{draft_sample}

Evaluate:
1. Pacing (too fast, too slow, just right)
2. Emotional impact
3. Reader engagement
4. Clarity
5. Overall reading experience

Format as JSON."""
        
        response = await self.llm_client.complete(system=system_prompt, user=user_prompt)
        
        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                return json.loads(response[json_start:json_end])
        except:
            pass
        
        return {"pacing": "good", "emotional_impact": "moderate", "engagement": "good"}
    
    async def _logic_consistency_check(self, project: BookProject) -> List[str]:
        """Logic & Consistency Agent checks for plot holes."""
        system_prompt = """You are a Logic & Consistency Agent. Hunt for plot holes and inconsistencies."""
        
        outline_text = json.dumps(project.outline, indent=2)[:1000] if project.outline else "No outline"
        draft_sample = project.full_draft[:2000] if project.full_draft else "No draft"
        
        user_prompt = f"""Check for plot holes and inconsistencies:

Outline:
{outline_text}

Draft Sample:
{draft_sample}

Identify:
1. Plot holes
2. Character inconsistencies
3. World-building contradictions
4. Timeline issues
5. Logic errors

Return as JSON array of issues."""
        
        response = await self.llm_client.complete(system=system_prompt, user=user_prompt)
        
        try:
            json_start = response.find('[')
            json_end = response.rfind(']') + 1
            if json_start >= 0 and json_end > json_start:
                return json.loads(response[json_start:json_end])
        except:
            pass
        
        return []
    
    async def _sensitivity_review(self, project: BookProject) -> List[str]:
        """Sensitivity/Alignment Agent review."""
        system_prompt = """You are a Sensitivity/Alignment Agent. Review for problematic content."""
        
        draft_sample = project.full_draft[:2000] if project.full_draft else "No draft"
        
        user_prompt = f"""Review for sensitivity and alignment issues:

Draft Sample:
{draft_sample}

Check for:
1. Problematic stereotypes
2. Offensive content
3. Misrepresentation
4. Ethical concerns
5. Content warnings needed

Return as JSON array of issues (empty if none found)."""
        
        response = await self.llm_client.complete(system=system_prompt, user=user_prompt)
        
        try:
            json_start = response.find('[')
            json_end = response.rfind(']') + 1
            if json_start >= 0 and json_end > json_start:
                return json.loads(response[json_start:json_end])
        except:
            pass
        
        return []
    
    async def _create_assessment(self, report: Dict[str, Any]) -> str:
        """Create overall QA assessment."""
        issues_count = len(report.get('logic_consistency_issues', [])) + len(report.get('sensitivity_issues', []))
        
        if issues_count == 0:
            return "Draft passes all quality checks. Ready for production."
        elif issues_count < 3:
            return f"Draft is mostly ready but has {issues_count} minor issues to address."
        else:
            return f"Draft requires significant revision. {issues_count} issues identified."
    
    async def _identify_changes(self, report: Dict[str, Any]) -> List[str]:
        """Identify recommended changes."""
        changes = []
        
        if report.get('logic_consistency_issues'):
            changes.extend([f"Fix: {issue}" for issue in report['logic_consistency_issues'][:5]])
        
        if report.get('sensitivity_issues'):
            changes.extend([f"Review: {issue}" for issue in report['sensitivity_issues'][:3]])
        
        test_feedback = report.get('test_reader_feedback', {})
        if test_feedback.get('pacing') == 'too slow':
            changes.append("Improve pacing in slower sections")
        elif test_feedback.get('pacing') == 'too fast':
            changes.append("Add more detail and development")
        
        return changes


class FormattingAgent(BaseAgent):
    """Formatting Agent - Assembles final manuscript."""
    
    def __init__(self, llm_client: LLMClient, message_bus: MessageBus):
        super().__init__("FormattingAgent", "Formatting Agent", llm_client, message_bus)
    
    async def format_manuscript(self, project: BookProject) -> str:
        """Format the final manuscript."""
        if not project.full_draft:
            return ""
        
        # Add table of contents
        toc = "# Table of Contents\n\n"
        if project.outline:
            for chapter in project.outline:
                toc += f"{chapter.get('chapter_number', 0)}. {chapter.get('title', 'Untitled')}\n"
        
        # Format main content
        formatted = f"{toc}\n\n{project.full_draft}"
        
        # Clean up formatting
        formatted = formatted.replace('\n\n\n', '\n\n')
        
        await self.send_message("CEO", Phase.INDUSTRIALIZATION_PACKAGING, 
                              f"Manuscript formatted: {len(formatted)} characters")
        
        return formatted


class ExportAgent(BaseAgent):
    """Export Agent - Prepares output formats."""
    
    def __init__(self, llm_client: LLMClient, message_bus: MessageBus):
        super().__init__("ExportAgent", "Export Agent", llm_client, message_bus)
    
    async def prepare_exports(self, project: BookProject) -> Dict[str, Any]:
        """Prepare exports in multiple formats."""
        exports = {}
        
        if project.formatted_manuscript:
            # Markdown export
            exports['markdown'] = project.formatted_manuscript
            
            # EPUB-ready text
            exports['epub_ready'] = self._prepare_epub_text(project.formatted_manuscript)
            
            # PDF export
            pdf_path = await self._generate_pdf(project)
            if pdf_path:
                exports['pdf_path'] = pdf_path
        
        await self.send_message("CEO", Phase.INDUSTRIALIZATION_PACKAGING, 
                              f"Exports prepared: {list(exports.keys())}")
        
        return exports
    
    def _prepare_epub_text(self, text: str) -> str:
        """Prepare text for EPUB conversion."""
        # Basic EPUB formatting
        return text.replace('# ', '## ').replace('\n\n', '\n')
    
    async def _generate_pdf(self, project: BookProject) -> Optional[str]:
        """Generate PDF file from formatted manuscript."""
        try:
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
            from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            from reportlab.lib import colors
        except ImportError:
            print("Warning: reportlab not installed. PDF export disabled.")
            print("Install with: pip install reportlab")
            return None
        
        if not project.formatted_manuscript:
            return None
        
        # Generate filename
        safe_title = "".join(c for c in (project.title or "Untitled") if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_title = safe_title.replace(' ', '_')[:50]  # Limit length
        pdf_path = f"{safe_title}_book.pdf"
        
        try:
            # Create PDF document
            doc = SimpleDocTemplate(
                pdf_path,
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            # Container for the 'Flowable' objects
            story = []
            
            # Define styles
            styles = getSampleStyleSheet()
            
            # Custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#1a1a1a'),
                spaceAfter=30,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold'
            )
            
            chapter_style = ParagraphStyle(
                'CustomChapter',
                parent=styles['Heading1'],
                fontSize=18,
                textColor=colors.HexColor('#2c3e50'),
                spaceAfter=12,
                spaceBefore=20,
                fontName='Helvetica-Bold'
            )
            
            section_style = ParagraphStyle(
                'CustomSection',
                parent=styles['Heading2'],
                fontSize=14,
                textColor=colors.HexColor('#34495e'),
                spaceAfter=10,
                spaceBefore=15,
                fontName='Helvetica-Bold'
            )
            
            subsection_style = ParagraphStyle(
                'CustomSubsection',
                parent=styles['Heading3'],
                fontSize=12,
                textColor=colors.HexColor('#34495e'),
                spaceAfter=8,
                spaceBefore=12,
                fontName='Helvetica'
            )
            
            body_style = ParagraphStyle(
                'CustomBody',
                parent=styles['Normal'],
                fontSize=11,
                textColor=colors.HexColor('#2c3e50'),
                spaceAfter=12,
                alignment=TA_JUSTIFY,
                fontName='Helvetica',
                leading=14
            )
            
            # Title page
            if project.title:
                story.append(Spacer(1, 2*inch))
                story.append(Paragraph(project.title, title_style))
                story.append(Spacer(1, 0.5*inch))
            
            if project.launch_package and project.launch_package.get('subtitle'):
                subtitle_style = ParagraphStyle(
                    'Subtitle',
                    parent=styles['Normal'],
                    fontSize=14,
                    textColor=colors.HexColor('#7f8c8d'),
                    alignment=TA_CENTER,
                    fontName='Helvetica-Italic'
                )
                story.append(Paragraph(project.launch_package['subtitle'], subtitle_style))
            
            story.append(Spacer(1, 1*inch))
            
            if project.premise:
                premise_style = ParagraphStyle(
                    'Premise',
                    parent=styles['Normal'],
                    fontSize=10,
                    textColor=colors.HexColor('#7f8c8d'),
                    alignment=TA_CENTER,
                    fontName='Helvetica',
                    leftIndent=50,
                    rightIndent=50
                )
                story.append(Paragraph(f"<i>{project.premise}</i>", premise_style))
            
            story.append(PageBreak())
            
            # Parse and add content
            lines = project.formatted_manuscript.split('\n')
            current_paragraph = []
            
            for line in lines:
                line = line.strip()
                
                if not line:
                    if current_paragraph:
                        # Add accumulated paragraph
                        text = ' '.join(current_paragraph)
                        story.append(Paragraph(text, body_style))
                        current_paragraph = []
                    continue
                
                # Check for headings
                if line.startswith('# '):
                    # Title/Chapter
                    if current_paragraph:
                        text = ' '.join(current_paragraph)
                        story.append(Paragraph(text, body_style))
                        current_paragraph = []
                    title_text = line[2:].strip()
                    if 'Chapter' in title_text or 'Table of Contents' in title_text:
                        story.append(PageBreak())
                    story.append(Paragraph(title_text, chapter_style))
                
                elif line.startswith('## '):
                    # Section
                    if current_paragraph:
                        text = ' '.join(current_paragraph)
                        story.append(Paragraph(text, body_style))
                        current_paragraph = []
                    story.append(Paragraph(line[3:].strip(), section_style))
                
                elif line.startswith('### '):
                    # Subsection
                    if current_paragraph:
                        text = ' '.join(current_paragraph)
                        story.append(Paragraph(text, body_style))
                        current_paragraph = []
                    story.append(Paragraph(line[4:].strip(), subsection_style))
                
                elif line.startswith('#### '):
                    # Sub-subsection
                    if current_paragraph:
                        text = ' '.join(current_paragraph)
                        story.append(Paragraph(text, body_style))
                        current_paragraph = []
                    story.append(Paragraph(line[5:].strip(), subsection_style))
                
                elif line.startswith('- ') or line.startswith('* '):
                    # List item
                    if current_paragraph:
                        text = ' '.join(current_paragraph)
                        story.append(Paragraph(text, body_style))
                        current_paragraph = []
                    list_text = line[2:].strip()
                    story.append(Paragraph(f"• {list_text}", body_style))
                
                else:
                    # Regular text
                    current_paragraph.append(line)
            
            # Add any remaining paragraph
            if current_paragraph:
                text = ' '.join(current_paragraph)
                story.append(Paragraph(text, body_style))
            
            # Build PDF
            doc.build(story)
            
            await self.send_message("CEO", Phase.INDUSTRIALIZATION_PACKAGING, 
                                  f"PDF generated: {pdf_path}")
            
            return pdf_path
            
        except Exception as e:
            print(f"Error generating PDF: {e}")
            await self.send_message("CEO", Phase.INDUSTRIALIZATION_PACKAGING, 
                                  f"PDF generation failed: {str(e)}")
            return None


class LaunchDirectorAgent(BaseAgent):
    """Launch Director - Creates marketing and launch materials."""
    
    def __init__(self, llm_client: LLMClient, message_bus: MessageBus):
        super().__init__("LaunchDirector", "Launch Director", llm_client, message_bus)
        self.marketing_agents = []
    
    async def create_launch_package(self, project: BookProject) -> Dict[str, Any]:
        """Create complete launch package."""
        package = {
            "title_options": await self._generate_title_options(project),
            "subtitle": await self._generate_subtitle(project),
            "tagline": await self._generate_tagline(project),
            "back_cover_blurb": await self._generate_back_cover(project),
            "store_description": await self._generate_store_description(project),
            "keywords": await self._generate_keywords(project),
            "categories": await self._generate_categories(project),
            "short_synopsis": await self._generate_synopsis(project)
        }
        
        await self.send_message("CEO", Phase.MARKETING_LAUNCH, 
                              f"Launch package created with {len(package)} components")
        
        return package
    
    async def _generate_title_options(self, project: BookProject) -> List[str]:
        """Generate title options."""
        system_prompt = """You are a Marketing Agent. Generate compelling book title options."""
        
        user_prompt = f"""Generate 5 title options for:

Premise: {project.premise}
Genre: {project.book_brief.get('genre', 'Fiction') if project.book_brief else 'Fiction'}
Current Title: {project.title or 'None'}

Return as JSON array of strings."""
        
        response = await self.llm_client.complete(system=system_prompt, user=user_prompt)
        
        try:
            json_start = response.find('[')
            json_end = response.rfind(']') + 1
            if json_start >= 0 and json_end > json_start:
                return json.loads(response[json_start:json_end])
        except:
            pass
        
        return [project.title or "Untitled"]
    
    async def _generate_subtitle(self, project: BookProject) -> str:
        """Generate subtitle."""
        system_prompt = """You are a Marketing Agent. Create a compelling subtitle."""
        
        user_prompt = f"""Create a subtitle for:

Title: {project.title}
Premise: {project.premise}

Return just the subtitle text."""
        
        response = await self.llm_client.complete(system=system_prompt, user=user_prompt)
        return response.strip().strip('"').strip("'")
    
    async def _generate_tagline(self, project: BookProject) -> str:
        """Generate tagline."""
        system_prompt = """You are a Marketing Agent. Create a memorable tagline."""
        
        user_prompt = f"""Create a tagline for:

Title: {project.title}
Premise: {project.premise}

Return just the tagline text."""
        
        response = await self.llm_client.complete(system=system_prompt, user=user_prompt)
        return response.strip().strip('"').strip("'")
    
    async def _generate_back_cover(self, project: BookProject) -> str:
        """Generate back cover blurb."""
        system_prompt = """You are a Marketing Agent. Write a compelling back cover blurb."""
        
        user_prompt = f"""Write a back cover blurb for:

Title: {project.title}
Premise: {project.premise}
Synopsis: {project.launch_package.get('short_synopsis', '') if project.launch_package else ''}

Write 2-3 paragraphs that hook the reader without spoiling the story."""
        
        response = await self.llm_client.complete(system=system_prompt, user=user_prompt)
        return response.strip()
    
    async def _generate_store_description(self, project: BookProject) -> str:
        """Generate store description."""
        return await self._generate_back_cover(project)  # Can be customized
    
    async def _generate_keywords(self, project: BookProject) -> List[str]:
        """Generate keywords."""
        system_prompt = """You are a Marketing Agent. Generate SEO keywords."""
        
        user_prompt = f"""Generate 10 keywords for:

Title: {project.title}
Genre: {project.book_brief.get('genre', 'Fiction') if project.book_brief else 'Fiction'}
Premise: {project.premise}

Return as JSON array."""
        
        response = await self.llm_client.complete(system=system_prompt, user=user_prompt)
        
        try:
            json_start = response.find('[')
            json_end = response.rfind(']') + 1
            if json_start >= 0 and json_end > json_start:
                return json.loads(response[json_start:json_end])
        except:
            pass
        
        return []
    
    async def _generate_categories(self, project: BookProject) -> List[str]:
        """Generate categories."""
        genre = project.book_brief.get('genre', 'Fiction') if project.book_brief else 'Fiction'
        return [genre, "Literature", "Fiction"]
    
    async def _generate_synopsis(self, project: BookProject) -> str:
        """Generate short synopsis."""
        system_prompt = """You are a Marketing Agent. Write a compelling short synopsis."""
        
        user_prompt = f"""Write a 2-3 sentence synopsis for:

Title: {project.title}
Premise: {project.premise}

Make it engaging and concise."""
        
        response = await self.llm_client.complete(system=system_prompt, user=user_prompt)
        return response.strip()


class FerrariBookCompany:
    """Main orchestrator for the Ferrari-style book creation company."""
    
    def __init__(self):
        """Initialize the company with all agents."""
        agent_config = get_config()
        
        # Create LLM client
        self.llm_client = LLMClient(
            api_key=None,
            base_url=agent_config.get("base_url", "http://localhost:11434/v1"),
            model=agent_config.get("model", "llama3:latest"),
            provider=agent_config.get("provider", "local")
        )
        
        # Create message bus
        self.message_bus = MessageBus()
        
        # Create all agents
        self.ceo = CEOAgent(self.llm_client, self.message_bus)
        self.cpso = CPSOAgent(self.llm_client, self.message_bus)
        self.story_design_director = StoryDesignDirectorAgent(self.llm_client, self.message_bus)
        self.narrative_engineering_director = NarrativeEngineeringDirectorAgent(self.llm_client, self.message_bus)
        self.production_director = ProductionDirectorAgent(self.llm_client, self.message_bus)
        self.qa_director = QADirectorAgent(self.llm_client, self.message_bus)
        self.formatting_agent = FormattingAgent(self.llm_client, self.message_bus)
        self.export_agent = ExportAgent(self.llm_client, self.message_bus)
        self.launch_director = LaunchDirectorAgent(self.llm_client, self.message_bus)
        
        # Project state
        self.project: Optional[BookProject] = None
        self.owner_decisions: Dict[Phase, OwnerDecision] = {}
    
    async def create_book(self, title: Optional[str], premise: str, 
                         target_word_count: Optional[int] = None,
                         audience: Optional[str] = None,
                         owner_callback: Optional[callable] = None) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Main entry point: Create a book from idea to launch.
        
        Args:
            title: Working title (optional)
            premise: Short idea/premise
            target_word_count: Target word count (optional)
            audience: Target audience (optional)
            owner_callback: Function to call for owner decisions
                           Signature: (phase, summary, artifacts) -> OwnerDecision
        
        Returns:
            Tuple of (final_book_package, full_chat_log)
        """
        # Initialize project
        self.project = BookProject(
            title=title,
            premise=premise,
            target_word_count=target_word_count,
            audience=audience
        )
        
        # Set owner callback if provided
        if owner_callback:
            self.ceo._owner_callback = owner_callback
        
        # Run all phases
        phases = [
            Phase.STRATEGY_CONCEPT,
            Phase.EARLY_DESIGN,
            Phase.DETAILED_ENGINEERING,
            Phase.PROTOTYPES_TESTING,
            Phase.INDUSTRIALIZATION_PACKAGING,
            Phase.MARKETING_LAUNCH
        ]
        
        for phase in phases:
            self.project.current_phase = phase
            
            print(f"\n{'='*60}")
            print(f"PHASE: {phase.value.upper().replace('_', ' ')}")
            print(f"{'='*60}\n")
            
            # Execute phase
            await self._execute_phase(phase)
            
            # Get owner decision
            artifacts, decision = await self.ceo.coordinate_phase(phase, self.project)
            
            # Handle owner decision
            if decision == OwnerDecision.STOP:
                print("\nProject stopped by Owner.")
                break
            elif decision == OwnerDecision.REQUEST_CHANGES:
                print("\nOwner requested changes. Re-running phase...")
                # Re-run phase (simplified - in production would handle specific changes)
                await self._execute_phase(phase)
                artifacts, decision = await self.ceo.coordinate_phase(phase, self.project)
            
            self.owner_decisions[phase] = decision
            
            if decision == OwnerDecision.APPROVE:
                print(f"\n✓ Phase {phase.value} approved by Owner.")
        
        # Mark complete
        self.project.current_phase = Phase.COMPLETE
        self.project.status = "complete"
        
        # Assemble final package
        final_package = self._assemble_final_package()
        
        # Get full chat log
        chat_log = self.message_bus.get_chat_log()
        
        return final_package, chat_log
    
    async def _execute_phase(self, phase: Phase):
        """Execute a specific phase."""
        if phase == Phase.STRATEGY_CONCEPT:
            # CPSO creates book brief
            brief = await self.cpso.create_book_brief(
                self.project.premise,
                self.project.title,
                self.project.target_word_count,
                self.project.audience
            )
            self.project.book_brief = brief
            self.project.genre = brief.get('genre')
        
        elif phase == Phase.EARLY_DESIGN:
            # Story Design Director runs workshop
            design_results = await self.story_design_director.run_design_workshop(
                self.project.book_brief or {},
                self.project.premise
            )
            self.project.world_dossier = design_results.get('world_dossier')
            self.project.character_bible = design_results.get('character_bible')
            self.project.plot_arc = design_results.get('plot_arc')
        
        elif phase == Phase.DETAILED_ENGINEERING:
            # Narrative Engineering Director creates outline
            outline = await self.narrative_engineering_director.create_outline(self.project)
            self.project.outline = outline
        
        elif phase == Phase.PROTOTYPES_TESTING:
            # Production Director creates draft
            draft_chapters = await self.production_director.create_draft(self.project)
            self.project.draft_chapters = draft_chapters
            
            # QA Director tests
            revision_report = await self.qa_director.test_and_review(self.project)
            self.project.revision_report = revision_report
        
        elif phase == Phase.INDUSTRIALIZATION_PACKAGING:
            # Formatting Agent formats
            formatted = await self.formatting_agent.format_manuscript(self.project)
            self.project.formatted_manuscript = formatted
            
            # Export Agent prepares exports
            exports = await self.export_agent.prepare_exports(self.project)
            self.project.owner_edits['exports'] = exports
        
        elif phase == Phase.MARKETING_LAUNCH:
            # Launch Director creates package
            launch_package = await self.launch_director.create_launch_package(self.project)
            self.project.launch_package = launch_package
    
    def _assemble_final_package(self) -> Dict[str, Any]:
        """Assemble the final book package."""
        package = {
            "title": self.project.title,
            "premise": self.project.premise,
            "book_brief": self.project.book_brief,
            "world_dossier": self.project.world_dossier,
            "character_bible": self.project.character_bible,
            "plot_arc": self.project.plot_arc,
            "outline": self.project.outline,
            "full_draft": self.project.full_draft,
            "formatted_manuscript": self.project.formatted_manuscript,
            "revision_report": self.project.revision_report,
            "launch_package": self.project.launch_package,
            "exports": self.project.owner_edits.get('exports', {}),
            "status": self.project.status
        }
        
        # Add PDF path if available
        exports = self.project.owner_edits.get('exports', {})
        if 'pdf_path' in exports:
            package['pdf_path'] = exports['pdf_path']
        
        return package
    
    def get_chat_log(self, phase: Optional[Phase] = None) -> List[Dict[str, Any]]:
        """Get the chat log, optionally filtered by phase."""
        return self.message_bus.get_chat_log(phase)


# Main function for CLI usage
async def main():
    """CLI entry point."""
    import os
    
    print("=" * 60)
    print("Ferrari-Style Book Creation Company")
    print("=" * 60)
    print()
    
    # Get owner input
    title = input("Working title (optional, press Enter to skip): ").strip() or None
    premise = input("Short idea/premise (1-3 sentences): ").strip()
    
    if not premise:
        print("Error: Premise is required!")
        return
    
    word_count_input = input("Target word count (optional, press Enter to skip): ").strip()
    target_word_count = int(word_count_input) if word_count_input else None
    
    audience = input("Target audience (optional, press Enter to skip): ").strip() or None
    
    # Ask about output directory
    output_dir_input = input("Output directory (press Enter for 'book_outputs'): ").strip()
    output_directory = output_dir_input if output_dir_input else "book_outputs"
    
    # Owner callback for decisions
    def owner_decision_callback(phase, summary, artifacts):
        print(f"\n{summary}")
        print("\nOptions:")
        print("1. Approve and continue")
        print("2. Request changes")
        print("3. Stop project")
        
        choice = input("\nYour decision (1/2/3): ").strip()
        if choice == "1":
            return OwnerDecision.APPROVE
        elif choice == "2":
            return OwnerDecision.REQUEST_CHANGES
        else:
            return OwnerDecision.STOP
    
    # Create company and run
    company = FerrariBookCompany()
    final_package, chat_log = await company.create_book(
        title=title,
        premise=premise,
        target_word_count=target_word_count,
        audience=audience,
        owner_callback=owner_decision_callback
    )
    
    # Save results to output directory
    import json
    from pathlib import Path
    import shutil
    
    # Create output directory (use the one specified by user)
    output_dir = Path(output_directory)
    output_dir.mkdir(exist_ok=True)
    
    # Generate safe filename from title
    safe_title = "".join(c for c in (title or "Untitled") if c.isalnum() or c in (' ', '-', '_')).strip()
    safe_title = safe_title.replace(' ', '_')[:50] if safe_title else "Untitled"
    
    # Save JSON package
    json_filename = output_dir / f"{safe_title}_package.json"
    with open(json_filename, "w", encoding="utf-8") as f:
        json.dump(final_package, f, indent=2, ensure_ascii=False)
    
    # Save chat log
    chat_log_filename = output_dir / f"{safe_title}_chat_log.json"
    with open(chat_log_filename, "w", encoding="utf-8") as f:
        json.dump(chat_log, f, indent=2, ensure_ascii=False)
    
    # Copy PDF if it exists
    pdf_source_path = None
    pdf_dest_path = None
    
    if 'pdf_path' in final_package and final_package['pdf_path']:
        pdf_source_path = Path(final_package['pdf_path'])
        if pdf_source_path.exists():
            pdf_dest_path = output_dir / f"{safe_title}_book.pdf"
            import shutil
            shutil.copy2(pdf_source_path, pdf_dest_path)
    elif 'exports' in final_package and 'pdf_path' in final_package.get('exports', {}):
        pdf_source_path = Path(final_package['exports']['pdf_path'])
        if pdf_source_path.exists():
            pdf_dest_path = output_dir / f"{safe_title}_book.pdf"
            import shutil
            shutil.copy2(pdf_source_path, pdf_dest_path)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"✓ Book creation complete!")
    print(f"{'='*60}")
    print(f"\n📁 All files saved to: {output_dir.absolute()}/")
    print(f"\n📄 Generated Files:")
    print(f"  • JSON Package: {json_filename}")
    print(f"  • Chat Log: {chat_log_filename}")
    
    if pdf_dest_path and pdf_dest_path.exists():
        print(f"  • PDF Book: {pdf_dest_path}")
    else:
        print(f"  • PDF: Not generated (install reportlab for PDF export)")
    
    print(f"\n📊 Statistics:")
    print(f"  • Total messages: {len(chat_log)}")
    print(f"  • Chapters: {len(final_package.get('outline', []))}")
    if final_package.get('full_draft'):
        word_count = len(final_package['full_draft'].split())
        print(f"  • Word count: {word_count:,}")
    
    print(f"\n💡 To download files:")
    print(f"  • JSON: {json_filename.absolute()}")
    if pdf_dest_path and pdf_dest_path.exists():
        print(f"  • PDF: {pdf_dest_path.absolute()}")
    
    # Offer to open directory
    try:
        import platform
        if platform.system() == "Windows":
            os.startfile(output_dir.absolute())
        elif platform.system() == "Darwin":  # macOS
            os.system(f"open {output_dir.absolute()}")
        else:  # Linux
            os.system(f"xdg-open {output_dir.absolute()}")
        print(f"\n📂 Opened output directory in file manager")
    except:
        pass


if __name__ == "__main__":
    import asyncio
    import sys
    
    # Check for required dependencies before importing
    missing_deps = []
    
    try:
        import structlog
    except ImportError:
        missing_deps.append("structlog")
    
    try:
        import httpx
    except ImportError:
        missing_deps.append("httpx")
    
    if missing_deps:
        print("=" * 60)
        print("ERROR: Missing required dependencies")
        print("=" * 60)
        print(f"\nPlease install the following packages:")
        print(f"  pip install {' '.join(missing_deps)}")
        print(f"\nOr install all requirements:")
        print(f"  pip install -r requirements-app.txt")
        print(f"\nOr for book writer specifically:")
        print(f"  pip install -r app/book_writer/requirements.txt")
        sys.exit(1)
    
    # Now safe to import
    try:
        from app.llm.client import LLMClient
        from app.book_writer.config import get_config
    except ImportError as e:
        print(f"Error importing modules: {e}")
        print("\nMake sure you're running from the project root directory.")
        sys.exit(1)
    
    asyncio.run(main())

