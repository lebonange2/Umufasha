# Ferrari-Style Book Company - Complete Specification

## Message Bus Specification

### Architecture

The Message Bus is a central communication hub that:
- Logs all inter-agent messages
- Provides visibility to the Owner
- Supports message filtering by phase
- Enables agent subscriptions

### Message Structure

```python
@dataclass
class AgentMessage:
    from_agent: str          # Sender agent name
    to_agent: str            # Recipient agent name
    phase: Phase             # Current phase
    content: str             # Message content
    timestamp: datetime       # When sent
    message_type: str        # "internal", "owner_request", "owner_response"
```

### Message Types

1. **Internal**: Agent-to-agent communication
2. **Owner Request**: CEO presenting to Owner
3. **Owner Response**: Owner's decision/feedback

### Message Bus API

```python
class MessageBus:
    def send(from_agent, to_agent, phase, content, message_type="internal")
        # Send message and log it
    
    def get_chat_log(phase=None)
        # Get all messages, optionally filtered by phase
    
    def subscribe(agent_name, callback)
        # Subscribe agent to receive messages
```

### Example Message Flow

```
CEO → CPSO: "Create book brief for: [premise]"
CPSO → CEO: "Book brief created: {...}"
CEO → Owner: "Phase complete. Approve, request changes, or stop?"
Owner → CEO: "APPROVE"
CEO → StoryDesignDirector: "Begin design workshop"
...
```

### Chat Log Format

```json
[
    {
        "from_agent": "CEO",
        "to_agent": "CPSO",
        "phase": "strategy_concept",
        "content": "Create book brief...",
        "timestamp": "2024-01-01T12:00:00",
        "message_type": "internal"
    },
    {
        "from_agent": "CEO",
        "to_agent": "Owner",
        "phase": "strategy_concept",
        "content": "Phase complete. Summary: ...",
        "timestamp": "2024-01-01T12:05:00",
        "message_type": "owner_request"
    }
]
```

## Agent Communication Protocol

### Base Agent Class

All agents inherit from `BaseAgent`:

```python
class BaseAgent:
    def __init__(self, name, role, llm_client, message_bus)
    async def send_message(to_agent, phase, content)
    async def receive_message(message)
    async def execute_task(task, context)
```

### Agent Responsibilities Matrix

| Agent | Phase 1 | Phase 2 | Phase 3 | Phase 4 | Phase 5 | Phase 6 |
|-------|---------|---------|---------|---------|---------|---------|
| CEO | Coordinates | Coordinates | Coordinates | Coordinates | Coordinates | Coordinates |
| CPSO | Creates brief | - | - | - | - | - |
| StoryDesignDirector | - | Runs workshop | - | - | - | - |
| NarrativeEngineeringDirector | - | - | Creates outline | - | - | - |
| ProductionDirector | - | - | - | Creates draft | - | - |
| QADirector | - | - | - | Tests & reviews | - | - |
| FormattingAgent | - | - | - | - | Formats | - |
| ExportAgent | - | - | - | - | Exports | - |
| LaunchDirector | - | - | - | - | - | Creates package |

## Phase Execution Flow

### Phase 1: Strategy & Concept

```
1. CEO sends message to CPSO: "Create book brief"
2. CPSO analyzes premise and creates brief
3. CPSO sends brief to CEO
4. CEO presents brief to Owner
5. Owner approves/requests changes/stops
6. If approved, proceed to Phase 2
```

**Output**: Book Brief (genre, audience, themes, constraints)

### Phase 2: Early Design

```
1. CEO sends message to StoryDesignDirector: "Run design workshop"
2. StoryDesignDirector coordinates:
   - Worldbuilding Designer: Creates world dossier
   - Character Designer: Creates character bible
   - Tone & Mood Agent: Creates tone guide
3. StoryDesignDirector creates plot arc
4. CEO presents results to Owner
5. Owner approves/requests changes/stops
```

**Output**: World dossier, character bible, plot arc

### Phase 3: Detailed Engineering

```
1. CEO sends message to NarrativeEngineeringDirector: "Create outline"
2. NarrativeEngineeringDirector uses multi-agent system:
   - Plot Engineers structure plot
   - Chapter Architects design chapters
   - Continuity agents maintain consistency
3. Creates full hierarchical outline
4. CEO presents outline to Owner
5. Owner approves/requests changes/stops
```

**Output**: Full hierarchical outline

### Phase 4: Prototypes & Testing

```
1. CEO sends message to ProductionDirector: "Create draft"
2. ProductionDirector coordinates:
   - Drafting Agents write chapters
   - Assembly Agent combines chapters
3. CEO sends message to QADirector: "Test and review"
4. QADirector coordinates:
   - Test Readers evaluate
   - Logic & Consistency agents check
   - Sensitivity agents review
5. QADirector creates revision report
6. CEO presents draft + report to Owner
7. Owner approves/requests changes/stops
```

**Output**: Full draft, revision report

### Phase 5: Industrialization & Packaging

```
1. CEO sends message to FormattingAgent: "Format manuscript"
2. FormattingAgent formats with TOC, headings
3. CEO sends message to ExportAgent: "Prepare exports"
4. ExportAgent creates markdown, EPUB-ready text
5. CEO presents production-ready package to Owner
6. Owner approves/requests changes/stops
```

**Output**: Formatted manuscript, exports

### Phase 6: Marketing & Launch

```
1. CEO sends message to LaunchDirector: "Create launch package"
2. LaunchDirector coordinates marketing agents:
   - Generate title options
   - Create subtitle, tagline
   - Write back-cover blurb
   - Generate keywords, categories
   - Create synopsis
3. CEO presents launch package to Owner
4. Owner gives final sign-off
```

**Output**: Complete launch package

## Owner Interaction Protocol

### Owner Decision Points

At each phase completion:
1. CEO presents summary
2. CEO shows key artifacts
3. CEO asks: "Approve, request changes, or stop?"
4. Owner responds with decision
5. System acts on decision

### Owner Capabilities

- **View**: See all agent messages in chat log
- **Pause**: Stop at any phase gate
- **Modify**: Edit artifacts before approval
- **Cancel**: Stop project at any time
- **Request Changes**: Re-run phase with modifications

### Owner Decision Handling

```python
if decision == OwnerDecision.APPROVE:
    # Move to next phase
    proceed_to_next_phase()
elif decision == OwnerDecision.REQUEST_CHANGES:
    # Re-run current phase
    # In production: handle specific change requests
    rerun_current_phase()
elif decision == OwnerDecision.STOP:
    # Cancel project
    cancel_project()
```

## Main Function Specification

### Function Signature

```python
async def create_book(
    title: Optional[str],
    premise: str,
    target_word_count: Optional[int] = None,
    audience: Optional[str] = None,
    owner_callback: Optional[callable] = None
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]
```

### Parameters

- `title`: Working title (optional)
- `premise`: Short idea/premise (1-3 sentences)
- `target_word_count`: Target word count (optional)
- `audience`: Target audience (optional)
- `owner_callback`: Function for owner decisions
  - Signature: `(phase, summary, artifacts) -> OwnerDecision`

### Returns

1. **Final Book Package** (Dict):
   - Complete book with all phases' outputs
   - Ready for export/use

2. **Full Chat Log** (List[Dict]):
   - All inter-agent messages
   - Owner requests/responses
   - Complete communication history

### Execution Flow

```
1. Initialize project
2. For each phase:
   a. Execute phase (agents work)
   b. Present to Owner
   c. Get Owner decision
   d. Handle decision
3. Assemble final package
4. Return package + chat log
```

## Example Usage

### Programmatic

```python
from app.book_writer.ferrari_company import (
    FerrariBookCompany, OwnerDecision, Phase
)

async def create_my_book():
    company = FerrariBookCompany()
    
    def owner_decides(phase, summary, artifacts):
        print(f"\n{summary}")
        # Owner reviews and decides
        return OwnerDecision.APPROVE
    
    package, chat_log = await company.create_book(
        title="Exile to Mars",
        premise="A man from Earth goes to live on Mars...",
        target_word_count=80000,
        owner_callback=owner_decides
    )
    
    return package, chat_log
```

### CLI

```bash
python -m app.book_writer.ferrari_company
```

Interactive prompts guide through:
1. Title input
2. Premise input
3. Settings input
4. Phase-by-phase decisions

## Output Format

### Final Book Package

```json
{
    "title": "Exile to Mars",
    "premise": "A man from Earth...",
    "book_brief": {
        "genre": "Science Fiction",
        "target_audience": "SF readers",
        "recommended_word_count": 80000,
        "core_themes": ["exploration", "civilization"],
        "tone": "narrative",
        "style": "third person"
    },
    "world_dossier": {...},
    "character_bible": {...},
    "plot_arc": {...},
    "outline": [...],
    "full_draft": "...",
    "formatted_manuscript": "...",
    "revision_report": {...},
    "launch_package": {
        "title_options": [...],
        "subtitle": "...",
        "tagline": "...",
        "back_cover_blurb": "...",
        "keywords": [...],
        "categories": [...],
        "short_synopsis": "..."
    },
    "exports": {
        "markdown": "...",
        "epub_ready": "..."
    },
    "status": "complete"
}
```

### Chat Log

```json
[
    {
        "from_agent": "CEO",
        "to_agent": "CPSO",
        "phase": "strategy_concept",
        "content": "Create book brief...",
        "timestamp": "2024-01-01T12:00:00",
        "message_type": "internal"
    },
    ...
]
```

## Integration Points

### With Existing System

- Uses existing `LLMClient`
- Uses existing `get_config()`
- Can use existing `MultiAgentBookGenerator` for outline
- Compatible with existing book writer structure

### Extensibility

- Easy to add new agents
- Easy to add new phases
- Easy to customize owner interaction
- Easy to add new export formats

## Performance Considerations

- Sequential phase execution (can be parallelized)
- Owner approval gates (can be automated for testing)
- Message logging (can be optimized)
- LLM calls (can be cached/batched)

## Error Handling

- Phase failures: Logged, presented to Owner
- Agent failures: Fallback to default behavior
- LLM errors: Graceful degradation
- Owner cancellation: Clean shutdown

## Security & Privacy

- All messages logged (consider privacy)
- Owner data in project state
- LLM interactions logged
- Export files created locally

