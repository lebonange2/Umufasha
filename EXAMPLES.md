# Usage Examples

Real-world examples of using the Brainstorming Assistant.

## Example 1: Product Ideation

### Scenario
You're brainstorming ideas for a new mobile app.

### Session Flow

```bash
# Start session
python app.py --project mobile-app-ideas
```

**You speak**: "I want to create a fitness app that gamifies workouts"

**Assistant responds**:
```
💡 Idea Expansion:

Conservative Variation:
- A fitness tracking app with achievement badges and progress streaks
- Focus on simple exercises and daily goals
- [fitness, mobile, gamification]

Bold Variation:
- A multiplayer fitness RPG where real workouts power your character
- Team battles, guild systems, and virtual rewards
- [fitness, gaming, social, innovation]

🎯 Next Steps:
1. Research existing fitness gamification apps
2. Survey target users about motivation factors
3. Prototype core game mechanics
```

**Commands you run**:
```
:tag <id1> mvp,priority
:promote <id1>
:todo Research competitors in fitness gamification space
:todo Create user survey with 10 questions
:cluster
```

**After 10 more ideas**:
```
:summarize
:export md
```

**Output**: `brainstorm/mobile-app-ideas/notes.md` with organized ideas, clusters, and action items.

---

## Example 2: Content Creation

### Scenario
Planning content for a YouTube channel.

### Session Flow

```bash
python app.py --project youtube-content
```

**Series of inputs**:
1. "Tutorial series on Python for beginners"
2. "Behind-the-scenes of my coding setup"
3. "Live coding challenges with viewers"
4. "Interviews with other developers"

**After each input**, assistant provides:
- Variations and angles
- Suggested tags
- Related action items

**Useful commands**:
```
:cluster                    # Groups into content themes
:summarize recent          # Quick recap of last few ideas
:search tutorial           # Find all tutorial-related ideas
:todo Script first Python tutorial
:todo Set up interview recording equipment
:export docx               # Create content calendar document
```

---

## Example 3: Problem Solving

### Scenario
Debugging a complex technical issue.

### Session Flow

```bash
python app.py --project bug-investigation
```

**You speak**: "Users reporting slow page load times on mobile"

**Assistant helps**:
- Breaks down potential causes
- Suggests investigation approaches
- Generates debugging checklist

**Your workflow**:
```
# Record each finding
"Database queries taking 2+ seconds"
"Images not optimized for mobile"
"No CDN caching configured"

# Organize
:cluster                    # Groups by category (DB, Frontend, Infrastructure)

# Plan fixes
:todo Add database indexes for user queries
:todo Implement lazy loading for images
:todo Set up CloudFlare CDN

# Track progress
:complete <action-id>       # Mark actions as done

# Document solution
:summarize
:export md                  # Share with team
```

---

## Example 4: Meeting Notes

### Scenario
Recording a team brainstorming meeting.

### Session Flow

```bash
python app.py --project team-meeting-2025-01-15
```

**During meeting**:
- Press `Space` when someone speaks an important point
- Release when done
- Assistant automatically extracts action items

**Example transcript**:
```
👤 User: "We need to improve onboarding flow"
🤖 Assistant: 
   - Audit current onboarding steps
   - Identify drop-off points
   - A/B test simplified flow
   [onboarding, ux, priority]

👤 User: "Marketing wants more social media content"
🤖 Assistant:
   - Create content calendar
   - Assign social media manager
   - Set up analytics tracking
   [marketing, content, action-required]
```

**After meeting**:
```
:cluster                    # Organize by department/theme
:summarize                  # Create meeting summary
:export docx                # Send to team
```

---

## Example 5: Creative Writing

### Scenario
Developing a novel plot.

### Session Flow

```bash
python app.py --project novel-outline
```

**Brainstorming**:
```
"Protagonist is a time traveler stuck in medieval times"
:tag <id> character,protagonist

"Main conflict: preventing a war without changing history"
:tag <id> plot,conflict
:promote <id>

"Love interest is a local blacksmith who suspects the truth"
:tag <id> character,romance

"Twist: the blacksmith is also a time traveler"
:tag <id> plot,twist
```

**Organization**:
```
:cluster                    # Creates: Characters, Plot Points, Settings, Themes
:search character          # Find all character ideas
:summarize cluster:<id>    # Summarize character cluster
```

**Planning**:
```
:todo Write character backstories
:todo Outline Act 1 chapters
:todo Research medieval blacksmithing
```

**Export**:
```
:export md                 # Create outline document
```

---

## Example 6: Research Notes

### Scenario
Collecting research for a paper or project.

### Session Flow

```bash
python app.py --project ml-research
```

**Recording findings**:
```
"Paper: Attention Is All You Need - introduces transformer architecture"
:tag <id> paper,transformers,foundational

"Key insight: self-attention mechanism scales better than RNNs"
:tag <id> insight,architecture

"Implementation detail: multi-head attention uses 8 heads"
:tag <id> technical,implementation
```

**Organization**:
```
:cluster                    # Groups: Foundational Papers, Techniques, Applications
:search attention          # Find attention-related notes
:summarize                 # Create literature review summary
```

**Citation management**:
```
:todo Add proper citations to all papers
:todo Create bibliography
:export md                 # Generate research notes document
```

---

## Example 7: Daily Journaling

### Scenario
Using as a voice journal.

### Session Flow

```bash
python app.py --project journal-2025-01
```

**Daily entries**:
```
# Morning
"Goal for today: finish the project proposal"
:tag <id> goals,work

# Evening
"Completed the proposal, feeling accomplished"
:tag <id> achievements,work

"Idea: start morning meditation routine"
:tag <id> personal,health
```

**Weekly review**:
```
:search achievements       # Review accomplishments
:summarize recent         # Weekly summary
:export md                # Save journal entry
```

---

## Example 8: Event Planning

### Scenario
Planning a conference or event.

### Session Flow

```bash
python app.py --project tech-conference-2025
```

**Brainstorming**:
```
"Keynote speaker: AI ethics expert"
:tag <id> speakers,keynote
:todo Research and contact potential speakers

"Workshop: Hands-on ML model deployment"
:tag <id> workshops,technical
:todo Find workshop facilitator

"Venue needs: 500 capacity, good AV setup"
:tag <id> logistics,venue
```

**Organization**:
```
:cluster                    # Creates: Speakers, Workshops, Logistics, Marketing
:todo Create event timeline
:todo Set up registration system
:export docx               # Create event plan document
```

---

## Tips for Effective Use

### 1. Tag Consistently
```
:tag <id> urgent,important
:tag <id> research,technical
:tag <id> personal,idea
```

### 2. Promote Key Ideas
```
:promote <id>              # Mark as key idea
```

### 3. Regular Clustering
```
# After every 10-15 ideas
:cluster
```

### 4. Use Search
```
:search <keyword>          # Find related ideas
```

### 5. Export Often
```
:export md                 # Save progress
```

### 6. Review Summaries
```
:summarize recent          # Last 10 ideas
:summarize session         # Entire session
:summarize cluster:<id>    # Specific cluster
```

---

## Advanced Workflows

### Pomodoro Brainstorming
```bash
# 25-minute focused session
python app.py --project pomodoro-session-1

# Brainstorm intensely
# After 25 minutes:
:summarize
:export md
# Take 5-minute break
```

### Multi-Project Workflow
```bash
# Morning: Work project
python app.py --project work-tasks

# Afternoon: Side project
python app.py --project side-project

# Evening: Personal
python app.py --project personal-goals
```

### Collaborative Brainstorming
```bash
# One person records, others speak
python app.py --project team-brainstorm

# After session, share:
:export md
:export docx
# Send files to team
```

---

## Command Cheat Sheet

```bash
# Recording
Space          # Push-to-talk
R + Enter      # Record with auto-stop

# Organization
:tag <id> <tags>           # Add tags
:promote <id>              # Mark as key idea
:del <id>                  # Delete idea
:cluster                   # Generate clusters
:dedupe                    # Find duplicates

# Actions
:todo <text>               # Add action item
:complete <id>             # Mark action done

# Analysis
:search <query>            # Search ideas
:summarize [scope]         # Generate summary

# Export
:export md                 # Markdown
:export docx               # Word document
:export csv                # Spreadsheet

# System
:save                      # Save now
:config                    # Show config
:help                      # Show help
Q                          # Quit
```
