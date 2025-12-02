# Multi-Agent Book Generation System

## Overview

This document describes the Manager-Writer multi-agent system for automated book generation. The system uses two specialized agents that work together to create detailed book outlines and optionally full prose.

## Architecture

### Agents

#### 1. Manager Agent (`ManagerAgent`)
**Role**: Project lead / editor in chief

**Responsibilities**:
- Interprets user input (title, premise) and creates book plan
- Defines story arc (beginning, middle, end)
- Instructs Writer agent with structured tasks
- Reviews Writer outputs for quality, consistency, and completeness
- Maintains global state (characters, world rules, timeline)
- Approves sections/chapters when ready

**Key Methods**:
- `create_book_plan()`: Creates overall book structure and story arc
- `instruct_writer_for_chapter_outline()`: Generates instruction message for chapter outline
- `instruct_writer_for_main_points()`: Generates instruction for filling main points
- `review_writer_output()`: Reviews and approves/rejects Writer output
- `approve_chapter()`: Marks chapter as approved

#### 2. Writer Agent (`WriterAgent`)
**Role**: Professional novelist

**Responsibilities**:
- Generates detailed chapter outlines based on Manager instructions
- Fills in section, subsection, and main-point descriptions
- Generates full narrative prose (optional)
- Follows style and content instructions
- Respects continuity constraints

**Key Methods**:
- `generate_chapter_outline()`: Creates chapter outline structure
- `generate_main_points()`: Fills in paragraph-level main points
- `generate_prose()`: Writes full narrative text (optional)

### Communication Protocol

Agents communicate using `AgentMessage` objects with the following structure:

```python
@dataclass
class AgentMessage:
    role: MessageRole  # MANAGER or WRITER
    task: str  # What needs to be done
    context_summary: str  # Relevant context
    constraints: Dict[str, Any]  # Rules and limitations
    expected_output_format: str  # Format specification
    feedback: Optional[str]  # For revision requests
```

### State Management

The `BookState` class maintains:
- Book metadata (title, premise, settings)
- Story elements (characters, world rules, timeline)
- Story arc (beginning, middle, end)
- Generated content (outline, chapters)

## Workflow

### Step 1: Input Phase
User provides:
- Working title
- 1-3 sentence premise
- Optional: target word count, number of chapters, tone/style

### Step 2: Book Planning
Manager agent:
1. Analyzes premise
2. Creates story arc (beginning, middle, end)
3. Identifies key characters
4. Defines worldbuilding elements
5. Determines chapter count

### Step 3: Outline Generation
For each chapter:
1. **Manager** creates instruction message with:
   - Chapter number and position in story arc
   - Required structure (sections, subsections)
   - Context from previous chapters
   - Constraints (tone, style, characters)

2. **Writer** generates chapter outline:
   - Chapter title
   - 2-3 Sections with titles
   - 2 Subsections per section with titles
   - 3-5 Main points per subsection (initial)

3. **Manager** reviews outline:
   - Checks quality (specific titles, not generic)
   - Checks completeness (all required elements)
   - Checks consistency (aligns with premise/arc)
   - Approves or requests revisions (max 3 attempts)

### Step 4: Main Point Filling
For each subsection:
1. **Manager** instructs Writer to fill/improve main points
2. **Writer** generates full sentences (10+ words) describing each paragraph
3. **Manager** reviews for:
   - Full sentences (not placeholders)
   - Story-specific content
   - Logical progression
4. Updates subsection with approved main points

### Step 5: Prose Generation (Optional)
If enabled:
1. **Manager** instructs Writer to expand subsection into prose
2. **Writer** generates full narrative text
3. **Manager** reviews for quality and consistency

### Step 6: Final Assembly
All approved content is assembled into:
- JSON structure
- Markdown file (optional)

## Example: Mars Story Flow

Given premise: "A man from Earth goes to live on Mars where there is an advanced civilization."

### Step 1: Book Planning
Manager creates:
- Story arc:
  - Beginning: Man receives invitation, leaves Earth
  - Middle: Arrives on Mars, discovers advanced civilization
  - End: Must decide to join or remain outsider
- Characters: Daniel (engineer), sister, Martians
- World rules: Martian civilization has watched Earth, strict rules

### Step 2: Chapter 1 Outline
Manager instructs Writer:
```
Create outline for Chapter 1 (beginning of story).
2 sections, 2 subsections each, 3 main points per subsection.
Context: Story begins with invitation from Mars.
```

Writer generates:
```json
{
  "chapter_title": "Exile to the Red World",
  "sections": [
    {
      "section_title": "Leaving Earth",
      "subsections": [
        {
          "subsection_title": "The Offer from Mars",
          "main_points": [...]
        },
        {
          "subsection_title": "Goodbyes on a Dying Planet",
          "main_points": [...]
        }
      ]
    },
    {
      "section_title": "Arrival on Mars",
      "subsections": [...]
    }
  ]
}
```

Manager reviews: ✓ Approved (titles are specific, structure complete)

### Step 3: Main Points
For "The Offer from Mars":
Manager instructs Writer:
```
Fill main points for Chapter 1, Section 1, Subsection 1.1.
Generate 3 full sentences describing what happens in each paragraph.
```

Writer generates:
```
[
  "Introduce Daniel, a tired Earth engineer living in a collapsing megacity, who secretly dreams of the stars.",
  "He receives a mysterious encrypted message inviting him to join an advanced Martian civilization that has watched Earth for decades.",
  "The message promises clean air, limitless energy, and a new life, but warns that he can never return to Earth."
]
```

Manager reviews: ✓ Approved (all are full sentences, story-specific)

### Step 4: Assembly
Final structure:
```
Chapter 1 – Exile to the Red World
Section 1 – Leaving Earth
Subsection 1.1 – The Offer from Mars
  • Introduce Daniel, a tired Earth engineer...
  • He receives a mysterious encrypted message...
  • The message promises clean air...
```

## Usage

### CLI Usage

```bash
python -m app.book_writer.multi_agent_system
```

Follow the prompts:
1. Enter book title
2. Enter premise (1-3 sentences)
3. Enter number of chapters (default: 25)
4. Enter tone (default: narrative)
5. Enter style (default: third person)
6. Generate prose? (y/n)

### Programmatic Usage

```python
from app.book_writer.multi_agent_system import MultiAgentBookGenerator

# Create generator
generator = MultiAgentBookGenerator(
    title="Exile to Mars",
    premise="A man from Earth goes to live on Mars where there is an advanced civilization.",
    num_chapters=25,
    tone="narrative",
    style="third person"
)

# Generate book
result = await generator.generate_book(generate_prose=False)

# Export to markdown
generator.export_to_markdown("output.md", include_prose=False)
```

### API Integration

The system can be integrated with the existing FastAPI routes. See `app/routes/book_writer.py` for integration examples.

## Extensibility

### Adding New Agents

To add a new agent (e.g., "Continuity Checker"):

1. Create agent class:
```python
class ContinuityCheckerAgent:
    def __init__(self, llm_client, book_state):
        self.llm_client = llm_client
        self.book_state = book_state
    
    async def check_continuity(self, content):
        # Check for continuity issues
        pass
```

2. Integrate into workflow:
```python
# In MultiAgentBookGenerator.generate_book()
checker = ContinuityCheckerAgent(self.llm_client, self.book_state)
issues = await checker.check_continuity(chapter_outline)
```

### Switching Modes

To switch from outline-only to full-prose mode:

```python
# Outline only
result = await generator.generate_book(generate_prose=False)

# With prose
result = await generator.generate_book(generate_prose=True)
```

## Design Decisions

1. **Modular Architecture**: Each agent is a separate class, making it easy to modify or replace components.

2. **Message Protocol**: Standardized communication format ensures clear instructions and feedback.

3. **State Management**: Centralized `BookState` maintains consistency across agents.

4. **Review Loop**: Manager reviews all Writer output, ensuring quality before approval.

5. **Revision Limits**: Maximum 3 revisions per chapter to prevent infinite loops.

6. **Fallback Parsing**: If JSON extraction fails, text parsing provides backup.

## Future Enhancements

- **Continuity Checker Agent**: Automatically checks for plot holes and inconsistencies
- **Style Enforcer Agent**: Ensures consistent writing style throughout
- **Illustration Prompter Agent**: Generates prompts for book illustrations
- **Chapter Summarizer Agent**: Creates chapter summaries for navigation
- **Character Tracker Agent**: Maintains detailed character profiles and development arcs

