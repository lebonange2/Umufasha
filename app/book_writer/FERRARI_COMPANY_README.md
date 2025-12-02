# Ferrari-Style Multi-Agent Book Creation Company

## Overview

This system implements a complete organizational structure where every role is an AI agent, mirroring Ferrari's car production pipeline but for book creation. The Owner (human user) has absolute override and can see all agent communications in a visible chat log.

## Organizational Structure

### Owner (Human User)
- **Role**: Ultimate decision maker with absolute override
- **Capabilities**:
  - See all agent messages in chat log
  - Pause, modify, or cancel at any point
  - Edit briefs, outlines, and drafts before next phase
  - Approve or request changes at each phase gate

### CEO Agent
- **Role**: Overall coordination and Owner communication
- **Responsibilities**:
  - Coordinates all phases
  - Presents phase results to Owner
  - Manages approval gates
  - Routes Owner feedback to relevant agents

### CPSO Agent (Chief Product/Story Officer)
- **Role**: Product strategy
- **Responsibilities**:
  - Analyzes user's idea
  - Creates Book Brief (genre, audience, length, themes, constraints)
  - Defines product strategy

### Story Design Director Agent
- **Role**: Head of Design
- **Team**:
  - **Worldbuilding Designer Agents**: Create world dossier
  - **Character Designer Agents**: Create character bible
  - **Tone & Mood Agents**: Define emotional and stylistic tone
- **Output**: World dossier, character bible, high-level plot arc

### Narrative Engineering Director Agent
- **Role**: Head of Engineering
- **Team**:
  - **Plot Engineers**: Structure plot
  - **Chapter Architects**: Design chapter structure
  - **Continuity & Lore Agents**: Maintain consistency
  - **Style & Voice Agents**: Ensure consistent voice
- **Output**: Full hierarchical outline (Chapters → Sections → Subsections → Main points)

### Production Director Agent
- **Role**: Head of Manufacturing
- **Team**:
  - **Drafting Agents**: Write chapters
  - **Assembly Agents**: Combine chapters into full draft
- **Output**: Complete draft manuscript

### QA Director Agent
- **Role**: Head of Testing & Quality
- **Team**:
  - **Test Reader Agents**: Evaluate pacing, emotional impact, engagement
  - **Logic & Consistency Agents**: Hunt for plot holes
  - **Sensitivity/Alignment Agents**: Review for problematic content
- **Output**: Revision report with recommended changes

### Formatting Agent
- **Role**: Industrialization
- **Responsibilities**:
  - Assemble final approved manuscript
  - Clean structure, consistent headings
  - Create table of contents
  - Format internal references

### Export Agent
- **Role**: Packaging
- **Responsibilities**:
  - Prepare outputs (markdown, EPUB-ready text)
  - Format for different platforms

### Launch Director Agent
- **Role**: Head of Marketing & Sales
- **Team**:
  - **Marketing Agents**: Create marketing materials
- **Output**: Launch package with:
  - Title options
  - Subtitle
  - Tagline
  - Back-cover blurb
  - Store description
  - Keywords
  - Categories
  - Short synopsis

## Phases (Ferrari Pipeline)

### Phase 1: Strategy & Concept (Book Strategy)
1. CEO + CPSO read user's idea
2. CPSO drafts Book Brief
3. CEO presents brief to Owner for edits/approval
4. Owner approves, requests changes, or stops

### Phase 2: Early Design (Story & World Design)
1. Story Design Director runs design workshop
2. Worldbuilding, Character, and Tone agents work
3. Output: world dossier, character bible, plot arc
4. CEO presents to Owner for approval

### Phase 3: Detailed Engineering (Narrative Engineering)
1. Narrative Engineering Director coordinates team
2. Plot Engineers, Chapter Architects, Continuity agents work
3. Output: full hierarchical outline
4. CEO presents outline to Owner for feedback/approval

### Phase 4: Prototypes & Testing (Drafts & QA)
1. Production Director's Drafting Agents write sample chapters, then full draft
2. QA Director's team tests:
   - Test Readers evaluate pacing, emotional impact
   - Logic & Consistency agents hunt plot holes
   - Sensitivity agents review for problematic content
3. QA Director produces Revision Report
4. Production Director assigns revisions
5. CEO presents pre-final draft + major changes to Owner

### Phase 5: Industrialization & Packaging
1. Formatting Agent assembles final manuscript
2. Export Agent prepares outputs (markdown, EPUB)
3. CEO shows "Production-Ready Book Package" to Owner

### Phase 6: Marketing & Launch
1. Launch Director's team creates:
   - Title options, subtitle, tagline
   - Back-cover blurb and store description
   - Keywords, categories, synopsis
2. CEO bundles Launch Package
3. Owner gives final sign-off

## Message Bus & Chat Log

### Message Structure

Every message includes:
- `from_agent`: Sender agent name
- `to_agent`: Recipient agent name
- `phase`: Current phase
- `content`: Message content
- `timestamp`: When message was sent
- `message_type`: "internal", "owner_request", or "owner_response"

### Chat Log Visibility

All messages are visible to the Owner as a chat transcript. The Owner can:
- See all inter-agent communications
- View messages filtered by phase
- Understand the decision-making process
- Track project progress

### Message Bus API

```python
# Send message
message_bus.send(from_agent, to_agent, phase, content, message_type)

# Get chat log
chat_log = message_bus.get_chat_log()  # All messages
chat_log = message_bus.get_chat_log(Phase.STRATEGY_CONCEPT)  # Filtered by phase

# Subscribe to messages
message_bus.subscribe(agent_name, callback_function)
```

## Usage

### Basic Usage

```python
from app.book_writer.ferrari_company import FerrariBookCompany, OwnerDecision, Phase

# Create company
company = FerrariBookCompany()

# Owner callback for decisions
def owner_callback(phase, summary, artifacts):
    print(f"\n{summary}")
    # Owner reviews and decides
    return OwnerDecision.APPROVE  # or REQUEST_CHANGES or STOP

# Create book
final_package, chat_log = await company.create_book(
    title="Exile to Mars",
    premise="A man from Earth goes to live on Mars where there is an advanced civilization.",
    target_word_count=80000,
    audience="Science Fiction readers",
    owner_callback=owner_callback
)

# Access results
print(f"Book: {final_package['title']}")
print(f"Total messages: {len(chat_log)}")
```

### CLI Usage

```bash
python -m app.book_writer.ferrari_company
```

Follow the prompts:
1. Enter working title (optional)
2. Enter premise (1-3 sentences)
3. Enter target word count (optional)
4. Enter target audience (optional)
5. At each phase, review and approve/request changes/stop

### Owner Interaction

At each phase gate, the Owner sees:
- Summary of what happened
- Key artifacts (brief, world/characters, outline, draft)
- Question: "Approve, request changes, or stop the project?"

Owner can:
- **Approve**: Move to next phase
- **Request Changes**: Re-run phase with modifications
- **Stop**: Cancel project

## Final Output

The system returns:

1. **Final Book Package** (Dict):
   - `title`: Book title
   - `premise`: Original premise
   - `book_brief`: Strategy document
   - `world_dossier`: World building
   - `character_bible`: Character documentation
   - `plot_arc`: Story arc
   - `outline`: Full hierarchical outline
   - `full_draft`: Complete manuscript
   - `formatted_manuscript`: Production-ready formatted text
   - `revision_report`: QA findings
   - `launch_package`: Marketing materials
   - `exports`: Formatted exports (markdown, EPUB)
   - `status`: Project status

2. **Full Chat Log** (List[Dict]):
   - All inter-agent messages
   - Owner requests and responses
   - Complete communication history
   - Timestamps for all messages

## Agent Responsibilities Detail

### CEO Agent
- Coordinates all phases
- Presents results to Owner
- Manages approval gates
- Routes Owner feedback

### CPSO Agent
- Analyzes premise
- Creates book brief with:
  - Genre classification
  - Target audience
  - Word count recommendations
  - Core themes
  - Tone and style
  - Constraints
  - Success criteria

### Story Design Director
- Runs design workshop
- Coordinates:
  - Worldbuilding (world dossier)
  - Character design (character bible)
  - Tone & mood (emotional guide)
  - Plot arc (high-level structure)

### Narrative Engineering Director
- Creates full hierarchical outline
- Uses multi-agent system for:
  - Chapter structure
  - Section organization
  - Subsection details
  - Main points per paragraph

### Production Director
- Coordinates drafting
- Manages:
  - Chapter writing
  - Draft assembly
  - Revision assignments

### QA Director
- Coordinates testing
- Manages:
  - Test reader evaluation
  - Logic consistency checks
  - Sensitivity reviews
  - Revision report creation

### Formatting Agent
- Formats final manuscript
- Creates:
  - Table of contents
  - Consistent headings
  - Clean structure

### Export Agent
- Prepares exports
- Formats for:
  - Markdown
  - EPUB-ready text
  - Other formats

### Launch Director
- Creates launch package
- Generates:
  - Title options
  - Marketing copy
  - Keywords
  - Categories
  - Synopses

## Extensibility

### Adding New Agents

```python
class NewAgent(BaseAgent):
    def __init__(self, llm_client, message_bus):
        super().__init__("NewAgent", "New Agent Role", llm_client, message_bus)
    
    async def execute_task(self, task, context):
        # Agent logic
        pass

# Integrate into company
company.new_agent = NewAgent(company.llm_client, company.message_bus)
```

### Customizing Phases

Modify `FerrariBookCompany._execute_phase()` to:
- Add new phases
- Change phase order
- Add custom logic

### Custom Owner Callbacks

```python
def custom_owner_callback(phase, summary, artifacts):
    # Custom logic for owner decisions
    # Can edit artifacts, request specific changes, etc.
    return OwnerDecision.APPROVE
```

## File Structure

```
app/book_writer/
├── ferrari_company.py          # Main implementation
├── FERRARI_COMPANY_README.md   # This file
└── ...
```

## Example Flow

1. **Owner Input**: "A man from Earth goes to live on Mars..."
2. **Phase 1**: CPSO creates book brief → Owner approves
3. **Phase 2**: Design workshop → World, characters, plot → Owner approves
4. **Phase 3**: Engineering creates outline → Owner approves
5. **Phase 4**: Production drafts → QA tests → Owner approves
6. **Phase 5**: Formatting & export → Owner approves
7. **Phase 6**: Launch package → Owner approves
8. **Complete**: Final book package + full chat log

## Key Features

✅ **Complete Organizational Structure**: Every Ferrari role is an AI agent
✅ **Owner Override**: Human user has absolute control
✅ **Visible Chat Log**: All communications visible to Owner
✅ **Phase Gates**: Owner approval required between phases
✅ **Multiple Specialized Agents**: Teams of agents, not single agents
✅ **Full Pipeline**: From idea to launch
✅ **Extensible**: Easy to add new agents or phases

## Next Steps

1. Test with your LLM service
2. Customize agent prompts if needed
3. Add custom agents for specific needs
4. Integrate with existing book writer system
5. Add parallel processing for faster generation

