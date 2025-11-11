# Book Writing Assistant

A distraction-free writing environment with AI-powered assistance for book writing, powered by React, TypeScript, and FastAPI.

## Features

- ✍️ **Distraction-free editor** with title and body editing
- 🤖 **AI-powered assistance** with multiple modes:
  - Autocomplete sentences
  - Continue writing paragraphs
  - Expand selected text
  - Summarize sections
  - Generate outlines
  - Rewrite with different tones
  - Q&A about selections
- 🔄 **Provider Selection**: Switch between OpenAI (ChatGPT) and Anthropic (Claude) in UI
- 📄 **Document Context**: Upload PDF, DOCX, TXT files for AI to reference
- 💾 **File management**: Open and save `.txt` files
- 📚 **Draft management**: Autosave every 10 seconds with version history (last 20 versions)
- ⚡ **Streaming AI responses** with real-time token delivery
- ⌨️ **Keyboard shortcuts**: Ctrl/Cmd+S (save), Ctrl/Cmd+O (open), Ctrl/Cmd+K (command palette), Tab (accept suggestion)
- 🎨 **Customizable**: Monospace font toggle, focus mode, AI settings

## Setup

### Prerequisites

- Node.js 18+ and npm/yarn
- Python 3.10+ with FastAPI backend running
- OpenAI API key (or compatible LLM endpoint)

### Installation

1. **Install frontend dependencies:**

```bash
cd writer
npm install
```

2. **Configure backend:**

Ensure your FastAPI app has the `/api/llm` endpoint configured (already included in `app/routes/writer.py`).

Set your API keys as environment variables (recommended):

```bash
# For OpenAI
export OPENAI_API_KEY=your-api-key-here

# For Claude (Anthropic)
export ANTHROPIC_API_KEY=sk-ant-your-api-key-here
```

Or in `.env` file:

```bash
OPENAI_API_KEY=your-api-key-here
ANTHROPIC_API_KEY=sk-ant-your-api-key-here
```

**Note**: You can switch between providers in the UI without restarting the server.

### Development

1. **Start the FastAPI backend:**

```bash
# From project root
./start.sh
# Or
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

2. **Start the Vite dev server:**

```bash
cd writer
npm run dev
```

3. **Access the writer:**

Open http://localhost:8000/writer in your browser.

### Production Build

1. **Build the React app:**

```bash
cd writer
npm run build
```

This will output the built files to `app/static/writer/`.

2. **Start the FastAPI server:**

```bash
./start.sh
```

The writer will be available at http://localhost:8000/writer.

## Usage

### Basic Writing

1. Type in the editor - your document is autosaved every 10 seconds
2. Edit the title in the header
3. Use keyboard shortcuts:
   - `Ctrl/Cmd+S`: Save as `.txt` file
   - `Ctrl/Cmd+O`: Open `.txt` file
   - `Ctrl/Cmd+K`: Open command palette (future feature)
   - `Tab`: Accept inline AI suggestion
   - `Esc`: Dismiss inline suggestion
   - `Ctrl/Cmd+Enter`: Continue writing

### AI Features

#### Autocomplete

When you pause typing for 600ms, the AI will suggest a completion for your current sentence. Press `Tab` to accept or `Esc` to dismiss.

#### Continue Writing

Click "Continue Writing" in the AI Toolbox to have the AI continue from your cursor position. The response streams in real-time.

#### Expand Selection

1. Select some text
2. Click "Expand Selection" in the AI Toolbox
3. Set target word count
4. Click "Expand"

#### Other Actions

- **Summarize Section**: Select text and click "Summarize Section"
- **Generate Outline**: Click "Generate Outline" to create a hierarchical outline from your draft
- **Rewrite Tone**: Select text, choose a tone (plain, vivid, academic, humorous), and rewrite
- **Ask About This**: Select text and ask questions about it

### Version History

1. Click "History" in the top bar
2. Browse your autosaved versions
3. Click a version to restore it

### Settings

In the AI Toolbox (right sidebar):

- **AI Provider**: Choose between "OpenAI (ChatGPT)" or "Anthropic (Claude)"
- **Model**: LLM model name (updates based on provider)
  - OpenAI: gpt-4o, gpt-4-turbo, gpt-4, gpt-3.5-turbo
  - Claude: claude-3-5-sonnet-20241022, claude-3-opus, claude-3-haiku, etc.
- **Temperature**: 0-1, controls randomness (default: 0.7)
- **Max Tokens**: Maximum tokens per request (default: 1000)
- **Send full context**: Send entire document vs. recent context only
- **Respect outline constraints**: When generating outlines
- **Safe mode**: Block explicit content

### Document Context

1. Click "📁 Documents & Context" in the AI Toolbox
2. Upload PDF, DOCX, or TXT files (up to 50MB)
3. Select documents to use as context (checkbox)
4. Add custom text context if needed
5. AI will reference selected documents in all operations

See [Document Context Guide](README_writer_documents.md) for details.

## Architecture

### Frontend

- **React 18** with TypeScript
- **Vite** for build tooling
- **Tailwind CSS** for styling
- **React Query** for state management
- **IndexedDB** (with localStorage fallback) for storage

### Backend

- **FastAPI** endpoint at `/api/llm`
- **Server-Sent Events (SSE)** for streaming responses
- **LLMClient** abstraction supporting OpenAI-compatible APIs

### File Structure

```
writer/
├── src/
│   ├── pages/writer/       # Main page component
│   ├── features/writer/     # Feature components
│   │   ├── WriterEditor.tsx
│   │   ├── AIToolbox.tsx
│   │   ├── InlineSuggest.tsx
│   │   └── promptBuilders.ts
│   └── lib/                 # Utilities
│       ├── llmAdapter.ts    # LLM API client
│       ├── storage.ts       # Draft/version storage
│       ├── fileIO.ts        # File operations
│       └── types.ts         # TypeScript types
├── tests/
│   ├── unit/               # Vitest unit tests
│   └── e2e/                # Playwright E2E tests
└── package.json
```

## API Contract

### POST /api/llm

Request:

```json
{
  "system": "You are a helpful writing assistant...",
  "prompt": "user prompt",
  "context": "recent document window or selection",
  "mode": "autocomplete|continue|expand|summarize|outline|rewrite|qa",
  "params": {
    "temperature": 0.7,
    "max_tokens": 1000,
    "target_words": 100,
    "tone": "vivid"
  },
  "stream": true
}
```

Response (SSE stream):

```
data: {"token": "word ", "done": false}
data: {"token": "by ", "done": false}
...
data: {"token": "", "done": true}
```

## Testing

### Unit Tests

```bash
cd writer
npm test
```

### E2E Tests

```bash
cd writer
npm run test:e2e
```

Make sure the FastAPI server is running before running E2E tests.

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl/Cmd+S` | Save as `.txt` |
| `Ctrl/Cmd+O` | Open `.txt` file |
| `Ctrl/Cmd+K` | Open command palette (future) |
| `Tab` | Accept inline suggestion |
| `Esc` | Dismiss inline suggestion |
| `Ctrl/Cmd+Enter` | Continue writing |

## Privacy & Performance

- **Context windowing**: By default, only the last ~1200 tokens are sent for quick actions
- **Full context toggle**: Enable "Send full context" to send entire document
- **No content tracking**: Suggestions are not logged or tracked
- **Offline support**: Editor works offline; AI features require network

## Troubleshooting

### Writer page not loading

1. Check that FastAPI server is running on port 8000
2. Check browser console for errors
3. In development, ensure Vite dev server is running on port 5173

### AI features not working

1. Check that `/api/llm` endpoint is accessible
2. Verify API keys are set:
   - For OpenAI: `export OPENAI_API_KEY=your-key`
   - For Claude: `export ANTHROPIC_API_KEY=sk-ant-your-key`
3. Check browser network tab for API errors
4. See [API Key Setup](API_KEY_SETUP.md) for troubleshooting
5. See [Quick Fix: Anthropic](QUICK_FIX_ANTHROPIC.md) for Claude-specific issues

### Build errors

1. Ensure Node.js 18+ is installed
2. Run `npm install` in the `writer/` directory
3. Check TypeScript errors: `npm run build`

## Related Documentation

- **[Document Context Feature](README_writer_documents.md)** - Upload and use documents
- **[Provider Selection Guide](PROVIDER_SELECTION_GUIDE.md)** - Switch between AI providers
- **[Claude API Setup](CLAUDE_API_SETUP.md)** - Configure Claude/Anthropic API
- **[API Key Setup](API_KEY_SETUP.md)** - Environment variable configuration

## Future Enhancements

- [ ] Collaborative editing
- [ ] Citation management
- [ ] Export to Markdown, DOCX, PDF
- [ ] Custom themes
- [ ] Plugin system
- [ ] Multi-document workspace
- [ ] AI chat sidebar
- [ ] Grammar checking
- [ ] Word count goals
- [ ] Document search within uploaded files
- [ ] Highlight/cite specific document sections

## License

Same as main project license.

