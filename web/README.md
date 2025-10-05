# 🌐 Web Interface for Brainstorming Assistant

A beautiful, modern web interface for the Voice-Driven Brainstorming Assistant.

## Features

✨ **Modern UI** - Beautiful dark theme with smooth animations  
🎤 **Voice Recording** - Click-to-record with visual feedback  
💬 **Real-time Transcript** - See your conversation as it happens  
💡 **Idea Management** - View, promote, tag, and delete ideas  
🤖 **AI Assistant** - Get intelligent suggestions in real-time  
📊 **Live Statistics** - Track your brainstorming progress  
📁 **Clusters & Actions** - Organized view of related ideas and tasks  
📤 **Export** - Download in multiple formats (MD, DOCX, CSV, JSON)  

## Quick Start

### 1. Install Dependencies

```bash
# From the main ASSISTANT directory
pip install flask flask-socketio python-socketio
```

### 2. Run the Web Server

```bash
# From the ASSISTANT directory
python3 web/app.py
```

### 3. Open in Browser

Navigate to: **http://localhost:5000**

## Usage

### Recording Ideas

1. **Click the "Start Recording" button** (or press it again to stop)
2. **Speak your idea** clearly into your microphone
3. **Wait for transcription** - it will appear in the conversation panel
4. **AI Assistant responds** automatically with suggestions

### Managing Ideas

- **Promote**: Click the ⭐ icon to mark as a key idea
- **Delete**: Click the 🗑️ icon to remove an idea
- **View Tags**: Tags appear below each idea
- **Filter**: Use All/Key/Recent buttons to filter ideas

### Exporting

1. Click the **Export** button in the header
2. Choose your format:
   - **Markdown** - For documentation
   - **Word** - For presentations
   - **CSV** - For spreadsheets
   - **JSON** - For data analysis

## Architecture

```
web/
├── app.py                 # Flask backend
├── templates/
│   └── index.html        # Main HTML template
├── static/
│   ├── css/
│   │   └── style.css     # Styles
│   └── js/
│       └── app.js        # Frontend logic
└── README.md             # This file
```

## API Endpoints

### Session Management
- `POST /api/session/create` - Create new session
- `GET /api/session/data` - Get current session data

### Voice & Transcription
- `POST /api/transcribe` - Transcribe audio to text

### Idea Management
- `POST /api/idea/tag` - Tag an idea
- `POST /api/idea/promote` - Promote an idea
- `POST /api/idea/delete` - Delete an idea

### Actions
- `POST /api/action/add` - Add action item

### Export
- `GET /api/export/<format>` - Export session

## Configuration

The web interface uses the same configuration as the terminal app:

- **STT Backend**: Set in `.env` (default: whisper_local)
- **LLM Backend**: Set in `.env` (default: openai)
- **API Keys**: Set `OPENAI_API_KEY` environment variable

## Browser Compatibility

✅ Chrome/Edge 90+  
✅ Firefox 88+  
✅ Safari 14+  
✅ Opera 76+  

**Note**: Requires browser support for:
- MediaRecorder API (for audio recording)
- Web Audio API (for audio processing)
- Fetch API (for AJAX requests)

## Troubleshooting

### Microphone Not Working

1. **Grant permissions**: Browser will ask for microphone access
2. **Check settings**: Ensure microphone is selected in browser settings
3. **HTTPS required**: Some browsers require HTTPS for mic access (use localhost for development)

### Transcription Fails

1. **Check backend**: Ensure Whisper model is loaded
2. **Check logs**: Look at terminal output for errors
3. **Audio quality**: Speak clearly and reduce background noise

### No AI Responses

1. **Check API key**: Ensure `OPENAI_API_KEY` is set
2. **Check connection**: Verify internet connection
3. **Check logs**: Look for LLM initialization errors

## Development

### Running in Debug Mode

```bash
# Enable Flask debug mode
export FLASK_DEBUG=1
python3 web/app.py
```

### Modifying the UI

- **Styles**: Edit `static/css/style.css`
- **Layout**: Edit `templates/index.html`
- **Logic**: Edit `static/js/app.js`
- **Backend**: Edit `app.py`

### Adding Features

1. Add API endpoint in `app.py`
2. Add frontend function in `app.js`
3. Update UI in `index.html` if needed
4. Style in `style.css`

## Production Deployment

### Using Gunicorn

```bash
pip install gunicorn eventlet
gunicorn --worker-class eventlet -w 1 -b 0.0.0.0:5000 web.app:app
```

### Using Docker

```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
EXPOSE 5000
CMD ["python3", "web/app.py"]
```

### Nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name brainstorm.example.com;
    
    location / {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

## Security Notes

- **HTTPS**: Use HTTPS in production for secure mic access
- **API Keys**: Never expose API keys in frontend code
- **Sessions**: Uses secure session cookies
- **CORS**: Configure CORS for production deployments

## Performance

- **Auto-refresh**: Session data refreshes every 5 seconds
- **Lazy loading**: Only loads visible content
- **Optimized**: Minimal JavaScript, efficient rendering

## Future Enhancements

- [ ] Real-time collaboration (WebSocket)
- [ ] Voice activity detection visualization
- [ ] Drag-and-drop idea organization
- [ ] Custom themes
- [ ] Mobile app (PWA)
- [ ] Offline mode
- [ ] Multi-language support

## Support

For issues or questions:
1. Check the main [README.md](../README.md)
2. Review [QUICKSTART.md](../QUICKSTART.md)
3. Open an issue on GitHub

---

**Built with**: Flask, Vanilla JavaScript, and modern CSS
