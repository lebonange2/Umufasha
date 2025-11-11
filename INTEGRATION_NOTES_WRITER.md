# Writer Integration Notes

## Quick Start

1. **Install dependencies:**
```bash
cd writer
npm install
```

2. **Build the React app:**
```bash
npm run build
```

3. **Start the FastAPI server:**
```bash
# From project root
./start.sh
```

4. **Access at:** http://localhost:8000/writer

## Development Mode

For development with hot reload:

1. **Terminal 1 - Start FastAPI:**
```bash
./start.sh
```

2. **Terminal 2 - Start Vite dev server:**
```bash
cd writer
npm run dev
```

3. **Access at:** http://localhost:8000/writer (will proxy to Vite dev server)

## File Structure

```
ASSISTANT/
├── app/
│   ├── routes/
│   │   └── writer.py          # Backend API endpoint
│   ├── llm/
│   │   └── client.py          # Updated with streaming support
│   ├── static/
│   │   └── writer/            # Built React app (after npm run build)
│   └── main.py                # Updated with /writer route
└── writer/                    # React app source
    ├── src/
    │   ├── pages/writer/
    │   ├── features/writer/
    │   └── lib/
    ├── tests/
    └── package.json
```

## Backend Changes

1. **New route:** `app/routes/writer.py` - `/api/llm` endpoint
2. **Updated:** `app/llm/client.py` - Added `stream()` method
3. **Updated:** `app/main.py` - Added `/writer` route and static file mounting

## Environment Variables

Ensure these are set in `.env`:

```bash
OPENAI_API_KEY=your-api-key-here
LLM_BASE_URL=https://api.openai.com/v1  # Optional, defaults to OpenAI
LLM_MODEL=gpt-4o                         # Optional, defaults to gpt-4o
```

## API Endpoint

The `/api/llm` endpoint accepts:

```json
{
  "system": "System prompt (optional)",
  "prompt": "User prompt",
  "context": "Document context",
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

Returns Server-Sent Events (SSE) stream with tokens.

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

## Production Deployment

1. Build the React app:
```bash
cd writer
npm run build
```

2. The built files will be in `app/static/writer/`

3. Start FastAPI server - it will automatically serve the built files at `/writer`

## Troubleshooting

### "Cannot GET /writer"
- Ensure you've run `npm run build` in the `writer/` directory
- Check that `app/static/writer/index.html` exists

### AI features not working
- Check that `OPENAI_API_KEY` is set in `.env`
- Verify `/api/llm` endpoint is accessible (check browser network tab)
- Check FastAPI logs for errors

### Development mode issues
- Ensure Vite dev server is running on port 5173
- Check that FastAPI is proxying correctly (see `vite.config.ts`)

## Next Steps

1. Customize AI prompts in `writer/src/features/writer/promptBuilders.ts`
2. Add more AI modes by extending the `WriterMode` type
3. Customize UI in `writer/src/features/writer/` components
4. Add more keyboard shortcuts in `WriterEditor.tsx`

