# Ferrari Company UI Usage Guide

## Accessing the UI

1. Start your server:
   ```bash
   ./start.sh
   # or
   uvicorn app.main:app --reload
   ```

2. Navigate to:
   ```
   http://localhost:8000/writer/ferrari-company
   ```

   Or click the **"🏎️ Ferrari Company"** button from the main writer page.

## Using the UI

### Step 1: Create Project

1. Fill in the form:
   - **Working Title** (optional): Your book title
   - **Short Idea/Premise** (required): 1-3 sentences describing your story
   - **Target Word Count** (optional): Desired word count
   - **Target Audience** (optional): Target readers
   - **Output Directory**: Where to save files (default: `book_outputs`)

2. Click **"Create Project"**

### Step 2: Execute Phases

The UI follows the exact same pipeline as the CLI:

1. **Execute Phase**: Click **"▶ Execute Phase"** button
   - The system executes the current phase
   - You'll see progress messages
   - Phase artifacts are generated

2. **Review Results**: 
   - View the generated artifacts (book brief, world, outline, etc.)
   - Review the chat log to see agent communications

3. **Make Decision**:
   - **✓ Approve & Continue**: Move to next phase (auto-executes)
   - **↻ Request Changes**: Re-run current phase
   - **✗ Stop Project**: Cancel the project

4. **Auto-Progression**: 
   - When you approve, the next phase automatically executes
   - Same smooth flow as CLI
   - No manual phase execution needed after first approval

### Step 3: Download Files

Once the project status is **"complete"**, download buttons appear:

- **📦 Download Complete Archive (ZIP)**: All files in one archive
- **📥 Download JSON Package**: Complete book data
- **📄 Download PDF Book**: Formatted book PDF
- **💬 Download Chat Log**: Agent communications

## Pipeline Flow (Same as CLI)

```
1. Strategy & Concept
   → Execute → Review Brief → Approve

2. Early Design
   → Execute → Review World/Characters → Approve

3. Detailed Engineering
   → Execute → Review Outline → Approve

4. Prototypes & Testing
   → Execute → Review Draft/QA → Approve

5. Industrialization & Packaging
   → Execute → Review Formatted Manuscript → Approve

6. Marketing & Launch
   → Execute → Review Launch Package → Approve

7. Complete
   → Download Files
```

## Features

### Same Pipeline as CLI
- ✅ Uses exact same `FerrariBookCompany` class
- ✅ Same phase execution logic
- ✅ Same agent communication
- ✅ Same file generation
- ✅ No differences in output

### UI Enhancements
- ✅ Visual phase progress
- ✅ Real-time chat log viewing
- ✅ Artifact preview
- ✅ One-click downloads
- ✅ Auto-progression between phases

### Chat Log
- Click **"Show Chat Log"** to see all agent communications
- View messages filtered by phase
- See the complete conversation history

## Tips

1. **Review Each Phase**: Don't skip reviewing artifacts
2. **Use Chat Log**: Understand agent decisions
3. **Request Changes**: Don't hesitate to request changes if needed
4. **Download ZIP**: Easiest way to get all files
5. **Auto-Progression**: After first approval, phases auto-execute

## Troubleshooting

### Issue: Phase not executing
**Solution**: Make sure you clicked "Execute Phase" for the first phase

### Issue: Download buttons not appearing
**Solution**: Wait for status to be "complete" (all 6 phases approved)

### Issue: Files not downloading
**Solution**: Check browser download settings, files are generated on server

## Comparison: UI vs CLI

| Feature | CLI | UI |
|---------|-----|-----|
| Pipeline | ✅ Same | ✅ Same |
| Agents | ✅ Same | ✅ Same |
| Output | ✅ Same | ✅ Same |
| Files | ✅ Same | ✅ Same |
| Experience | Terminal | Web Browser |
| Downloads | Manual (SCP/etc) | One-click buttons |

**Result**: Identical book generation, different interface!

