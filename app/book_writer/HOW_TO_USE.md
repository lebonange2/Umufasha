# How to Generate a Book and Download It

## Quick Start Guide

This guide shows you how to use the book writer system to generate a book and download it as JSON or PDF.

## Method 1: Using the Web Interface (Recommended)

### Step 1: Access the Book Writer

1. Start your FastAPI server:
   ```bash
   cd /home/uwisiyose/ASSISTANT
   uvicorn app.main:app --reload
   ```

2. Open your browser and navigate to:
   ```
   http://localhost:8000/writer
   ```

3. Click on the **"📚 Book Writer"** button or navigate to:
   ```
   http://localhost:8000/writer/book-writer
   ```

### Step 2: Create a New Project

1. Click the **"+ New"** button in the sidebar
2. Fill in the form:
   - **Book Title**: Enter your book title (e.g., "Exile to Mars")
   - **Initial Prompt**: Enter your premise (e.g., "A man from Earth goes to live on Mars where there is an advanced civilization.")
   - **Number of Chapters**: Enter desired number (default: 25)
3. Click **"Create Project"**

### Step 3: Generate the Outline

1. Select your project from the sidebar
2. Click the **"Generate Outline"** button
3. Wait for the outline generation to complete
4. Review the generated outline:
   - Check chapters, sections, subsections, and main points
   - Edit any part you want to change
   - Click **"Save Outline"** when satisfied

### Step 4: Generate the Book

1. Make sure you're in the **"Chapters"** view (toggle at the top)
2. Click the **"Generate Book"** button
   - Note: This button is only enabled when the outline is complete
   - If disabled, check the validation message and fill in missing parts
3. Wait for book generation to complete
   - This may take several minutes depending on the number of chapters
   - You'll see progress messages in the console

### Step 5: Download Your Book

Once the book status is **"complete"**, you'll see two download buttons:

1. **📥 Download JSON**: Downloads complete project data as JSON
   - Includes: project info, outline, all chapters
   - Useful for: backup, data export, further processing

2. **📄 Download PDF**: Downloads formatted book as PDF
   - Professional formatting with chapters
   - Ready to read or print
   - Requires reportlab to be installed

## Method 2: Using the Ferrari Company (CLI)

### Step 1: Install Dependencies

```bash
pip install structlog httpx reportlab
```

### Step 2: Run the Ferrari Company

```bash
python3 -m app.book_writer.ferrari_company
```

### Step 3: Follow the Prompts

1. **Working title** (optional): Enter your book title or press Enter
2. **Short idea/premise**: Enter 1-3 sentences describing your story
3. **Target word count** (optional): Enter desired word count or press Enter
4. **Target audience** (optional): Enter target audience or press Enter

### Step 4: Review and Approve Each Phase

The system will go through 6 phases:

1. **Strategy & Concept**: Review the book brief
   - Choose: 1 (Approve), 2 (Request Changes), or 3 (Stop)

2. **Early Design**: Review world, characters, and plot
   - Choose: 1 (Approve), 2 (Request Changes), or 3 (Stop)

3. **Detailed Engineering**: Review the full outline
   - Choose: 1 (Approve), 2 (Request Changes), or 3 (Stop)

4. **Prototypes & Testing**: Review draft and QA report
   - Choose: 1 (Approve), 2 (Request Changes), or 3 (Stop)

5. **Industrialization & Packaging**: Review formatted manuscript
   - Choose: 1 (Approve), 2 (Request Changes), or 3 (Stop)

6. **Marketing & Launch**: Review launch package
   - Choose: 1 (Approve), 2 (Request Changes), or 3 (Stop)

### Step 5: Access Generated Files

After completion, all files are saved in the output directory (default: `book_outputs/`):

- **{Book_Title}_package.json**: Complete book package with all data
- **{Book_Title}_chat_log.json**: Full agent communication log
- **{Book_Title}_book.pdf**: PDF file (if generated)

The system will:
- Create the output directory automatically
- Display full file paths
- Show statistics (messages, chapters, word count)
- Optionally open the directory in your file manager

**Example output:**
```
✓ Book creation complete!
============================================================

📁 All files saved to: /path/to/book_outputs/

📄 Generated Files:
  • JSON Package: Exile_to_Mars_package.json
  • Chat Log: Exile_to_Mars_chat_log.json
  • PDF Book: Exile_to_Mars_book.pdf

📊 Statistics:
  • Total messages: 45
  • Chapters: 25
  • Word count: 85,234

💡 To download files:
  • JSON: /path/to/book_outputs/Exile_to_Mars_package.json
  • PDF: /path/to/book_outputs/Exile_to_Mars_book.pdf
```

## Method 3: Programmatic Usage

### Using the Ferrari Company

```python
import asyncio
from app.book_writer.ferrari_company import (
    FerrariBookCompany, OwnerDecision, Phase
)

async def create_and_download_book():
    # Create company
    company = FerrariBookCompany()
    
    # Owner callback for decisions
    def owner_decides(phase, summary, artifacts):
        print(f"\n=== {phase.value.upper()} ===")
        print(summary)
        # Auto-approve for automation
        return OwnerDecision.APPROVE
    
    # Create book
    package, chat_log = await company.create_book(
        title="Exile to Mars",
        premise="A man from Earth goes to live on Mars where there is an advanced civilization.",
        target_word_count=80000,
        owner_callback=owner_decides
    )
    
    # Access PDF path
    if 'pdf_path' in package:
        print(f"PDF saved to: {package['pdf_path']}")
    
    # Save JSON
    import json
    with open("my_book.json", "w") as f:
        json.dump(package, f, indent=2)
    
    return package, chat_log

# Run
asyncio.run(create_and_download_book())
```

## Troubleshooting

### Issue: "Generate Book" button is disabled

**Solution**: 
- Check the outline validation message
- Make sure all chapters have sections, subsections, and main points
- Fill in any missing parts and click "Save Outline"

### Issue: PDF download fails

**Solution**:
```bash
pip install reportlab
```

### Issue: Book generation takes too long

**Solution**:
- This is normal - each chapter requires LLM generation
- For faster generation, reduce the number of chapters
- Use a faster LLM model if available

### Issue: Download buttons don't appear

**Solution**:
- Make sure book status is "complete"
- Make sure chapters have been generated
- Refresh the page

## File Locations

### Web Interface Downloads
- Files download directly to your browser's default download folder
- Filenames: `{Book_Title}_book.json` and `{Book_Title}_book.pdf`

### CLI Downloads
- Files saved in current working directory
- `book_package.json`: Complete package
- `chat_log.json`: Agent communications
- `{Book_Title}_book.pdf`: PDF file

## Tips

1. **Start Small**: Test with 3-5 chapters first
2. **Review Outline**: Always review and edit the outline before generating
3. **Save Often**: Use "Save Outline" after making edits
4. **Check Status**: Wait for status to be "complete" before downloading
5. **Backup**: Download JSON regularly as backup

## Next Steps

- Edit chapters individually after generation
- Export to other formats (EPUB, DOCX) - coming soon
- Share your generated books
- Use the outline as a writing guide

