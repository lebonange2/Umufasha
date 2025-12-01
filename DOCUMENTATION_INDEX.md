# Documentation Index

Complete guide to all documentation for the AI Assistant project.

## 🚀 Getting Started

### Quick Start Guides
- **[README.md](README.md)** - Main project overview and quick start
- **[QUICKSTART.md](QUICKSTART.md)** - Get up and running in minutes
- **[HOW_TO_RUN.md](HOW_TO_RUN.md)** - Detailed setup and running instructions

### Setup & Configuration
- **[API_KEY_SETUP.md](API_KEY_SETUP.md)** - Configure API keys (OpenAI, Claude)
- **[env.example](env.example)** - Environment variable template

## ✍️ Writer Assistant

### Core Documentation
- **[README_writer.md](README_writer.md)** - Complete Writer Assistant guide
- **[INTEGRATION_NOTES_WRITER.md](INTEGRATION_NOTES_WRITER.md)** - Integration details

### Features
- **[README_writer_documents.md](README_writer_documents.md)** - Document upload and context feature
- **[PROVIDER_SELECTION_GUIDE.md](PROVIDER_SELECTION_GUIDE.md)** - Switch between AI providers in UI
- **[CLAUDE_API_SETUP.md](CLAUDE_API_SETUP.md)** - Configure Claude/Anthropic API
- **[QUICK_FIX_ANTHROPIC.md](QUICK_FIX_ANTHROPIC.md)** - Troubleshoot Claude API issues

## 🤖 AI Provider Configuration

### Provider Selection
- **[PROVIDER_SELECTION_GUIDE.md](PROVIDER_SELECTION_GUIDE.md)** - Runtime provider switching
- **[CLAUDE_API_SETUP.md](CLAUDE_API_SETUP.md)** - Claude API setup
- **[API_KEY_SETUP.md](API_KEY_SETUP.md)** - Environment variable setup

### Troubleshooting
- **[QUICK_FIX_ANTHROPIC.md](QUICK_FIX_ANTHROPIC.md)** - Fix Claude API errors
- **[API_KEY_SETUP.md](API_KEY_SETUP.md)** - API key troubleshooting

## 🧪 Testing & Development

- **[TESTING_GUIDE.md](TESTING_GUIDE.md)** - Comprehensive testing instructions
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Contribution guidelines

## 🏗️ Architecture & Technical

- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture overview
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Production deployment guide
- **[CODING_ENVIRONMENT_INTEGRATION.md](CODING_ENVIRONMENT_INTEGRATION.md)** - Coding environment integration

## 📚 Feature Documentation

### Personal Assistant
- **[README.md](README.md)** - Main features and workflows
- **[TESTING_GUIDE.md](TESTING_GUIDE.md)** - Testing instructions

### Brainstorming
- **[mcp/README.md](mcp/README.md)** - Brainstorming assistant docs
- **[mcp/QUICK_START_BRAIN.md](mcp/QUICK_START_BRAIN.md)** - Quick start

### Coding Environment
- **[CODING_ENVIRONMENT_INTEGRATION.md](CODING_ENVIRONMENT_INTEGRATION.md)** - Integration guide
- **[USING_CODING_ENVIRONMENT.md](USING_CODING_ENVIRONMENT.md)** - Usage guide

## 🔧 Troubleshooting

### Common Issues
- **[QUICK_FIX_ANTHROPIC.md](QUICK_FIX_ANTHROPIC.md)** - Claude API 401 errors
- **[API_KEY_SETUP.md](API_KEY_SETUP.md)** - API key issues
- **[README_writer.md](README_writer.md)** - Writer Assistant troubleshooting

### Error Messages
- **"ANTHROPIC_API_KEY environment variable is not set"** → See [QUICK_FIX_ANTHROPIC.md](QUICK_FIX_ANTHROPIC.md)
- **"401 Unauthorized"** → See [API_KEY_SETUP.md](API_KEY_SETUP.md)
- **"400 Bad Request"** → Check API key configuration

## 📖 API Documentation

- **Interactive API Docs**: http://localhost:8000/docs (when server is running)
- **Health Check**: http://localhost:8000/health
- **Writer API**: `/api/llm` - LLM streaming endpoint
- **Document API**: `/api/writer/documents/*` - Document upload/management

## 🎯 Quick Reference

### Environment Variables

| Variable | Purpose | Required For |
|----------|---------|--------------|
| `OPENAI_API_KEY` | OpenAI API key | OpenAI provider |
| `ANTHROPIC_API_KEY` | Claude API key | Claude provider |
| `DATABASE_URL` | Database connection | All features |
| `REDIS_URL` | Redis connection | Caching/scheduling |

### Common Commands

```bash
# Setup
./setup.sh

# Start server
./start.sh

# Stop server
./stop.sh

# Run tests
./test.sh

# Build writer frontend
cd writer && npm run build
```

### Key URLs

- **Homepage**: http://localhost:8000/
- **Writer**: http://localhost:8000/writer
- **Admin**: http://localhost:8000/admin
- **API Docs**: http://localhost:8000/docs
- **Health**: http://localhost:8000/health

## 📝 Documentation by Topic

### Setup & Installation
1. [README.md](README.md) - Overview
2. [QUICKSTART.md](QUICKSTART.md) - Quick start
3. [HOW_TO_RUN.md](HOW_TO_RUN.md) - Detailed setup
4. [API_KEY_SETUP.md](API_KEY_SETUP.md) - API keys

### Writer Assistant

### Structure Feature
- **[Structure Feature Guide](writer/README_structure.md)** - Complete guide to hierarchical document structure
- **[Structure Quick Start](writer/QUICKSTART_STRUCTURE.md)** - Get started with structure mode in 5 minutes

## Writer Assistant (Legacy)
1. [README_writer.md](README_writer.md) - Main guide
2. [README_writer_documents.md](README_writer_documents.md) - Documents
3. [PROVIDER_SELECTION_GUIDE.md](PROVIDER_SELECTION_GUIDE.md) - Providers
4. [CLAUDE_API_SETUP.md](CLAUDE_API_SETUP.md) - Claude setup

### Troubleshooting
1. [QUICK_FIX_ANTHROPIC.md](QUICK_FIX_ANTHROPIC.md) - Claude errors
2. [API_KEY_SETUP.md](API_KEY_SETUP.md) - API key issues
3. [README_writer.md](README_writer.md#troubleshooting) - Writer issues

### Development
1. [TESTING_GUIDE.md](TESTING_GUIDE.md) - Testing
2. [CONTRIBUTING.md](CONTRIBUTING.md) - Contributing
3. [ARCHITECTURE.md](ARCHITECTURE.md) - Architecture

## 🔍 Finding What You Need

### "How do I..."
- **...set up the project?** → [QUICKSTART.md](QUICKSTART.md)
- **...configure API keys?** → [API_KEY_SETUP.md](API_KEY_SETUP.md)
- **...use the Writer Assistant?** → [README_writer.md](README_writer.md)
- **...upload documents?** → [README_writer_documents.md](README_writer_documents.md)
- **...switch between ChatGPT and Claude?** → [PROVIDER_SELECTION_GUIDE.md](PROVIDER_SELECTION_GUIDE.md)
- **...fix Claude API errors?** → [QUICK_FIX_ANTHROPIC.md](QUICK_FIX_ANTHROPIC.md)
- **...test the application?** → [TESTING_GUIDE.md](TESTING_GUIDE.md)
- **...deploy to production?** → [DEPLOYMENT.md](DEPLOYMENT.md)

### "I'm getting..."
- **...401 Unauthorized** → [API_KEY_SETUP.md](API_KEY_SETUP.md)
- **...400 Bad Request** → [QUICK_FIX_ANTHROPIC.md](QUICK_FIX_ANTHROPIC.md)
- **..."API key not set"** → [QUICK_FIX_ANTHROPIC.md](QUICK_FIX_ANTHROPIC.md)
- **...build errors** → [README_writer.md](README_writer.md#troubleshooting)

## 📚 Additional Resources

- **Examples**: [EXAMPLES.md](EXAMPLES.md)
- **Changelog**: [CHANGELOG.md](CHANGELOG.md)
- **Project Summary**: [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)

---

**Last Updated**: 2025-11-10  
**Maintained By**: AI Assistant Project

