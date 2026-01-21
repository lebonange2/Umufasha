# How to Run the Application Locally

This guide explains how to run the exam generator (and full application) locally on your computer using OpenAI API.

## Prerequisites

1. **Python 3.8+** installed
2. **Git** (to clone the repository if needed)
3. **OpenAI API Key** (for using OpenAI provider)

## Step 1: Clone/Setup the Repository

If you haven't already:

```bash
cd /path/to/your/projects
git clone <repository-url>
cd ASSISTANT
```

## Step 2: Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate

# On Windows:
# venv\Scripts\activate
```

## Step 3: Install Dependencies

```bash
# Make sure virtual environment is activated
pip install --upgrade pip
pip install -r requirements.txt
```

## Step 4: Set Environment Variables

### For OpenAI Provider (Recommended for Local)

Set the OpenAI API key as an environment variable:

```bash
# Linux/Mac - Add to your shell profile (~/.bashrc, ~/.zshrc, etc.)
export OPENAI_API_KEY=sk-your-openai-api-key-here
export LLM_PROVIDER=openai
export OPENAI_MODEL=gpt-4o

# Or set temporarily for current session:
export OPENAI_API_KEY=sk-your-key-here
export LLM_PROVIDER=openai
```

**Windows (PowerShell):**
```powershell
$env:OPENAI_API_KEY="sk-your-openai-api-key-here"
$env:LLM_PROVIDER="openai"
$env:OPENAI_MODEL="gpt-4o"
```

**Windows (Command Prompt):**
```cmd
set OPENAI_API_KEY=sk-your-openai-api-key-here
set LLM_PROVIDER=openai
set OPENAI_MODEL=gpt-4o
```

### Optional: Create .env File

You can also create a `.env` file in the project root (but remember to export the variables):

```bash
# .env file
LLM_PROVIDER=openai
OPENAI_MODEL=gpt-4o
# Note: OPENAI_API_KEY must be exported as environment variable
```

Then source it:
```bash
# Linux/Mac
export $(cat .env | xargs)
export OPENAI_API_KEY=sk-your-key-here  # Still need to export this
```

## Step 5: Initialize Database (First Time Only)

```bash
# Initialize the database
python3 scripts/init_db.py
```

## Step 6: Start the Application

### Option 1: Using Start Script (Recommended)

```bash
# Make sure virtual environment is activated
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Start the server
./start_server.sh
```

### Option 2: Using uvicorn Directly

```bash
# Activate virtual environment
source venv/bin/activate

# Start the server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Option 3: Using Python Module

```bash
# Activate virtual environment
source venv/bin/activate

# Start the server
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Step 7: Access the Application

Once the server is running, open your browser and navigate to:

- **Main Application**: http://localhost:8000
- **Exam Generator**: http://localhost:8000/writer/exam-generator
- **Writer Assistant**: http://localhost:8000/writer
- **API Documentation**: http://localhost:8000/docs
- **Admin Panel**: http://localhost:8000/admin
  - Default login: `admin` / `admin123`

## Using the Exam Generator

1. **Navigate to Exam Generator**:
   - Go to http://localhost:8000/writer/exam-generator

2. **Select Provider**:
   - Choose "OpenAI (GPT-4o)" from the Provider dropdown
   - The model will automatically switch to `gpt-4o`

3. **Create a Project**:
   - Upload a text file or paste content
   - Set number of problems per learning objective
   - Click "Create Project"

4. **Start Generation**:
   - Click "Start Generation"
   - Monitor progress in real-time
   - Download results when complete

## Troubleshooting

### "OPENAI_API_KEY is required" Error

**Solution:**
```bash
# Verify the environment variable is set
echo $OPENAI_API_KEY  # Linux/Mac
echo %OPENAI_API_KEY%  # Windows CMD
$env:OPENAI_API_KEY  # Windows PowerShell

# If not set, export it:
export OPENAI_API_KEY=sk-your-key-here  # Linux/Mac
set OPENAI_API_KEY=sk-your-key-here  # Windows CMD
$env:OPENAI_API_KEY="sk-your-key-here"  # Windows PowerShell

# Restart the server after setting
```

### Port 8000 Already in Use

**Solution:**
```bash
# Find what's using port 8000
lsof -i :8000  # Linux/Mac
netstat -ano | findstr :8000  # Windows

# Kill the process or use a different port:
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

### Module Not Found Errors

**Solution:**
```bash
# Make sure virtual environment is activated
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate  # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

### Database Errors

**Solution:**
```bash
# Reinitialize the database
python3 scripts/init_db.py

# Or delete and recreate
rm assistant.db  # Linux/Mac
del assistant.db  # Windows
python3 scripts/init_db.py
```

## Quick Start Summary

```bash
# 1. Setup (one time)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 scripts/init_db.py

# 2. Set environment variables (each session)
export OPENAI_API_KEY=sk-your-key-here
export LLM_PROVIDER=openai

# 3. Start server
source venv/bin/activate
./start_server.sh

# 4. Open browser
# http://localhost:8000/writer/exam-generator
```

## Making Environment Variables Persistent

### Linux/Mac

Add to `~/.bashrc` or `~/.zshrc`:

```bash
echo 'export OPENAI_API_KEY=sk-your-key-here' >> ~/.bashrc
echo 'export LLM_PROVIDER=openai' >> ~/.bashrc
source ~/.bashrc
```

### Windows

Add to System Environment Variables:
1. Open System Properties → Environment Variables
2. Add `OPENAI_API_KEY` with value `sk-your-key-here`
3. Add `LLM_PROVIDER` with value `openai`
4. Restart terminal/application

## Next Steps

- Read [OPENAI_LOCAL_SETUP.md](OPENAI_LOCAL_SETUP.md) for detailed OpenAI configuration
- Check [HOW_TO_RUN.md](HOW_TO_RUN.md) for more detailed instructions
- Visit http://localhost:8000/docs for API documentation

## Notes

- The application runs on **port 8000** by default
- Use `--reload` flag for development (auto-reload on code changes)
- The exam generator works with both OpenAI (local) and Ollama (RunPod) providers
- OpenAI API calls are made in parallel for faster generation
