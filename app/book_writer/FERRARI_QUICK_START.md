# Ferrari-Style Book Company - Quick Start Guide

## Overview

This guide shows you how to use the Ferrari-style multi-agent book creation company to create a book from idea to launch.

## Prerequisites

- Python 3.8+
- Access to LLM (local Ollama or remote API)
- Required dependencies installed

## Quick Start

### 1. CLI Usage (Easiest)

```bash
python -m app.book_writer.ferrari_company
```

You'll be prompted for:
- **Working title** (optional)
- **Premise** (1-3 sentences)
- **Target word count** (optional)
- **Target audience** (optional)

Then at each phase:
- Review the summary and artifacts
- Choose: Approve (1), Request Changes (2), or Stop (3)

### 2. Programmatic Usage

```python
import asyncio
from app.book_writer.ferrari_company import (
    FerrariBookCompany, OwnerDecision, Phase
)

async def create_book():
    # Create company
    company = FerrariBookCompany()
    
    # Define owner callback
    def owner_decides(phase, summary, artifacts):
        print(f"\n=== {phase.value.upper()} ===")
        print(summary)
        print("\nArtifacts:", list(artifacts.keys()))
        
        # In real usage, you'd show artifacts to user
        # For this example, auto-approve
        return OwnerDecision.APPROVE
    
    # Create book
    package, chat_log = await company.create_book(
        title="Exile to Mars",
        premise="A man from Earth goes to live on Mars where there is an advanced civilization.",
        target_word_count=80000,
        audience="Science Fiction readers",
        owner_callback=owner_decides
    )
    
    # Save results
    import json
    with open("book_package.json", "w") as f:
        json.dump(package, f, indent=2)
    
    with open("chat_log.json", "w") as f:
        json.dump(chat_log, f, indent=2)
    
    print(f"\n✓ Book created!")
    print(f"  Title: {package['title']}")
    print(f"  Status: {package['status']}")
    print(f"  Messages: {len(chat_log)}")

# Run
asyncio.run(create_book())
```

## Understanding the Phases

### Phase 1: Strategy & Concept
**What happens**: CPSO Agent creates a book brief
**You see**: Genre, audience, themes, constraints
**You decide**: Approve brief or request changes

### Phase 2: Early Design
**What happens**: Design workshop creates world, characters, plot
**You see**: World dossier, character bible, plot arc
**You decide**: Approve design or request changes

### Phase 3: Detailed Engineering
**What happens**: Engineering team creates full outline
**You see**: Hierarchical outline (chapters → sections → subsections → main points)
**You decide**: Approve outline or request changes

### Phase 4: Prototypes & Testing
**What happens**: Production writes draft, QA tests it
**You see**: Full draft + revision report
**You decide**: Approve draft or request changes

### Phase 5: Industrialization & Packaging
**What happens**: Formatting and export agents prepare final manuscript
**You see**: Formatted manuscript + exports (markdown, EPUB)
**You decide**: Approve package or request changes

### Phase 6: Marketing & Launch
**What happens**: Launch team creates marketing materials
**You see**: Title options, blurb, keywords, synopsis
**You decide**: Final approval

## Example: Mars Story

**Input**:
- Title: "Exile to Mars"
- Premise: "A man from Earth goes to live on Mars where there is an advanced civilization."

**Process**:
1. **Phase 1**: CPSO creates brief → "Science Fiction, 80k words, themes: exploration"
2. **Phase 2**: Design creates world/characters → "Martian civilization, Daniel character"
3. **Phase 3**: Engineering creates outline → "Chapter 1: Exile to the Red World..."
4. **Phase 4**: Production drafts → QA tests → "Draft complete, minor revisions"
5. **Phase 5**: Formatting → "Production-ready manuscript"
6. **Phase 6**: Launch package → "Title options, marketing copy"

**Output**:
- Complete book package (JSON)
- Full chat log (all agent messages)

## Viewing the Chat Log

```python
# Get all messages
chat_log = company.get_chat_log()

# Get messages for specific phase
phase_messages = company.get_chat_log(Phase.STRATEGY_CONCEPT)

# Print messages
for msg in chat_log:
    print(f"[{msg['timestamp']}] {msg['from_agent']} → {msg['to_agent']}")
    print(f"  {msg['content'][:100]}...")
```

## Customizing Owner Interaction

```python
def custom_owner_callback(phase, summary, artifacts):
    # Show artifacts to user
    if phase == Phase.STRATEGY_CONCEPT:
        print("Book Brief:", artifacts['book_brief'])
    elif phase == Phase.EARLY_DESIGN:
        print("World:", artifacts['world_dossier'])
        print("Characters:", artifacts['character_bible'])
    # ... etc
    
    # Get user decision
    decision = input("Approve (a), Request Changes (c), or Stop (s)? ")
    if decision == 'a':
        return OwnerDecision.APPROVE
    elif decision == 'c':
        return OwnerDecision.REQUEST_CHANGES
    else:
        return OwnerDecision.STOP
```

## Accessing Results

```python
# Final package contains everything
package = {
    'title': '...',
    'book_brief': {...},
    'world_dossier': {...},
    'character_bible': {...},
    'outline': [...],
    'full_draft': '...',
    'formatted_manuscript': '...',
    'launch_package': {...},
    'exports': {...}
}

# Access specific parts
outline = package['outline']
draft = package['full_draft']
marketing = package['launch_package']
```

## Tips

1. **Review Each Phase**: Don't skip phase reviews - they're important checkpoints
2. **Use Chat Log**: Check chat log to understand agent decisions
3. **Request Changes**: Don't hesitate to request changes if something isn't right
4. **Save Results**: Always save the package and chat log
5. **Customize Callbacks**: Create custom owner callbacks for your workflow

## Troubleshooting

### Issue: "LLM timeout"
**Solution**: Increase timeout in config or use faster LLM model

### Issue: "Phase taking too long"
**Solution**: This is normal - each phase does significant work. Be patient.

### Issue: "Owner callback not called"
**Solution**: Make sure you're providing the callback function correctly

### Issue: "Chat log empty"
**Solution**: Messages are logged as they're sent. Check that agents are actually sending messages.

## Next Steps

1. Read `FERRARI_COMPANY_README.md` for detailed documentation
2. Read `FERRARI_SPECIFICATION.md` for technical specs
3. Customize agent prompts if needed
4. Add custom agents for your needs
5. Integrate with your workflow

## Support

- Check chat log for detailed agent communications
- Review phase summaries for what happened
- Adjust owner callback for better interaction
- See documentation files for details

