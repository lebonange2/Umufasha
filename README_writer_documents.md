# Document Context Feature for Writer Assistant

## Overview

The Writer Assistant now supports uploading documents (PDF, DOCX, TXT) and adding custom text context to enhance AI writing assistance. The AI can reference these documents when generating content, making it perfect for research-based writing, academic papers, and content that needs to reference source materials.

## Features

### 📄 Document Upload
- **Supported Formats**: PDF, DOCX, DOC, TXT
- **File Size Limit**: 50MB per file
- **Automatic Text Extraction**: Documents are automatically processed and their text is extracted
- **Document Management**: Upload, view, select, and delete documents

### ✍️ Text Context
- **Custom Text Input**: Add any text as context (notes, research, quotes, etc.)
- **Persistent Storage**: Text context is saved and can be reused
- **Easy Management**: Toggle text context on/off as needed

### 🤖 AI Integration
- **Automatic Inclusion**: Selected documents and text context are automatically included in all AI requests
- **Smart Context**: AI uses document content to inform writing suggestions
- **All Modes Supported**: Works with autocomplete, continue writing, expand, summarize, outline, rewrite, and Q&A

## How to Use

### Uploading Documents

1. **Open Document Manager**:
   - Click the "📁 Documents & Context" button in the AI Toolbox (right sidebar)
   - The document manager panel will appear below the toolbox

2. **Upload a File**:
   - Click the "📁 Upload" button
   - Select a PDF, DOCX, or TXT file
   - Wait for upload and processing (text extraction happens automatically)

3. **Select Documents**:
   - Check the boxes next to documents you want to use as context
   - Selected documents are highlighted in blue
   - The count badge shows how many documents are selected

### Adding Text Context

1. **Enable Text Context**:
   - In the Document Manager, check "Add Text Context"
   - A text area will appear

2. **Enter Your Text**:
   - Type or paste any text you want to use as context
   - This could be notes, research findings, quotes, etc.

3. **Save**:
   - Click "Save Text Context" to store it
   - The text will be available for all AI operations

### Using Context in Writing

Once documents and/or text context are selected:

- **Autocomplete**: AI suggestions will consider your documents
- **Continue Writing**: AI will reference documents when continuing your draft
- **Expand**: AI will use document context when expanding selections
- **Summarize**: AI can summarize based on document content
- **Outline**: AI can generate outlines that reference your documents
- **Rewrite**: AI will maintain consistency with document style/content
- **Q&A**: Ask questions about your documents

## API Endpoints

### Upload Document
```bash
POST /api/writer/documents/upload
Content-Type: multipart/form-data

file: <file>
```

Response:
```json
{
  "success": true,
  "document": {
    "id": "uuid",
    "name": "document.pdf",
    "type": "application/pdf",
    "size": 12345,
    "text_preview": "First 500 chars...",
    "uploaded_at": "2024-01-01T12:00:00"
  },
  "text_length": 5000
}
```

### List Documents
```bash
GET /api/writer/documents
```

Response:
```json
{
  "success": true,
  "documents": [
    {
      "id": "uuid",
      "name": "document.pdf",
      "type": "application/pdf",
      "size": 12345,
      "text_preview": "...",
      "uploaded_at": "2024-01-01T12:00:00"
    }
  ]
}
```

### Get Document Text
```bash
GET /api/writer/documents/{doc_id}
```

### Delete Document
```bash
DELETE /api/writer/documents/{doc_id}
```

### Add Text Context
```bash
POST /api/writer/documents/{doc_id}/text
Content-Type: application/json

{
  "text": "Your custom text context here..."
}
```

## Technical Details

### File Processing

- **PDF**: Uses PyPDF2 to extract text from all pages
- **DOCX**: Uses python-docx to extract text from paragraphs
- **TXT**: Direct UTF-8 reading with fallback to latin-1 encoding

### Storage

- Documents are stored in `app/static/writer/uploads/`
- Each document has:
  - Original file: `{doc_id}.{extension}`
  - Extracted text: `{doc_id}.txt`
  - Metadata: `{doc_id}.meta.json`

### Context Integration

When making LLM requests, the system:
1. Loads text from selected document IDs
2. Includes custom text context
3. Combines with current document context
4. Sends all context to the LLM in a structured format

### Privacy & Performance

- Documents are stored locally on the server
- Only extracted text is sent to the LLM (not full files)
- Context is included only when documents are explicitly selected
- Large documents are automatically truncated if needed

## Example Workflow

1. **Research Phase**:
   - Upload research papers (PDFs)
   - Upload reference documents (DOCX)
   - Add notes as text context

2. **Writing Phase**:
   - Select relevant documents for your current section
   - Start writing
   - Use "Continue Writing" - AI will reference your documents
   - Use "Q&A" to ask questions about your research

3. **Refinement**:
   - Use "Expand" to add details based on documents
   - Use "Summarize" to condense document content
   - Use "Rewrite" to match document style

## Troubleshooting

### Upload Fails
- Check file size (max 50MB)
- Verify file type (PDF, DOCX, TXT only)
- Check server logs for errors

### Text Extraction Fails
- PDF: Ensure PDF is not encrypted or image-only
- DOCX: Ensure file is not corrupted
- Check server has required libraries (PyPDF2, python-docx)

### Documents Not Appearing in AI
- Ensure documents are selected (checkbox checked)
- Check that document text was extracted successfully
- Verify LLM request includes `document_context` parameter

## Dependencies

Required Python packages:
- `PyPDF2==3.0.1` - PDF text extraction
- `python-docx==1.1.0` - DOCX text extraction

Install if missing:
```bash
# Activate virtual environment first
source venv/bin/activate

# Install document processing libraries
pip install PyPDF2 python-docx
```

Note: These are already added to `requirements.txt` but may need to be installed if not already present.

## Future Enhancements

- [ ] Document search within uploaded files
- [ ] Highlight/cite specific document sections
- [ ] Document preview/viewer
- [ ] Batch document upload
- [ ] Document tagging/categorization
- [ ] OCR for image-based PDFs
- [ ] Support for more formats (EPUB, RTF, etc.)

