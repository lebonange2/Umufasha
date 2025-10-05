#!/usr/bin/env python3
"""Verify installation and setup of brainstorming assistant."""
import sys
import os
from pathlib import Path

# Colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def check(name, func):
    """Run a check and print result."""
    print(f"Checking {name}...", end=" ")
    try:
        result = func()
        if result:
            print(f"{GREEN}✓{RESET}")
            return True
        else:
            print(f"{RED}✗{RESET}")
            return False
    except Exception as e:
        print(f"{RED}✗ ({e}){RESET}")
        return False

def check_python_version():
    """Check Python version."""
    version = sys.version_info
    if version.major == 3 and version.minor >= 10:
        print(f"  Python {version.major}.{version.minor}.{version.micro}")
        return True
    return False

def check_dependencies():
    """Check if required packages are installed."""
    required = [
        'textual', 'rich', 'sounddevice', 'numpy', 
        'webrtcvad', 'dotenv', 'yaml'
    ]
    missing = []
    
    for package in required:
        try:
            if package == 'dotenv':
                __import__('dotenv')
            elif package == 'yaml':
                __import__('yaml')
            else:
                __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"\n  {RED}Missing: {', '.join(missing)}{RESET}")
        return False
    return True

def check_env_file():
    """Check if .env file exists."""
    return Path('.env').exists()

def check_config_file():
    """Check if config.yaml exists."""
    return Path('config.yaml').exists()

def check_audio():
    """Check audio devices."""
    try:
        import sounddevice as sd
        devices = sd.query_devices()
        input_devices = [d for d in devices if d['max_input_channels'] > 0]
        if input_devices:
            print(f"\n  Found {len(input_devices)} input device(s)")
            return True
        return False
    except:
        return False

def check_stt_backend():
    """Check if at least one STT backend is available."""
    backends = []
    
    try:
        from faster_whisper import WhisperModel
        backends.append('whisper_local')
    except ImportError:
        pass
    
    try:
        from vosk import Model
        backends.append('vosk')
    except ImportError:
        pass
    
    # Check for OpenAI key
    if os.getenv('OPENAI_API_KEY'):
        backends.append('whisper_api')
    
    if backends:
        print(f"\n  Available: {', '.join(backends)}")
        return True
    return False

def check_llm_backend():
    """Check if LLM backend is configured."""
    api_key = os.getenv('OPENAI_API_KEY')
    http_url = os.getenv('LLM_HTTP_URL')
    
    if api_key:
        print(f"\n  OpenAI API key configured")
        return True
    elif http_url:
        print(f"\n  HTTP LLM configured: {http_url}")
        return True
    return False

def check_file_structure():
    """Check if all required files exist."""
    required_files = [
        'app.py',
        'requirements.txt',
        'config.yaml',
        'audio/mic.py',
        'stt/base.py',
        'llm/base.py',
        'brain/model.py',
        'storage/files.py',
        'tui/main_view.py',
    ]
    
    missing = [f for f in required_files if not Path(f).exists()]
    
    if missing:
        print(f"\n  {RED}Missing files: {', '.join(missing)}{RESET}")
        return False
    return True

def main():
    """Run all checks."""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}🧠 Brainstorming Assistant - Setup Verification{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")
    
    checks = [
        ("Python version (3.10+)", check_python_version),
        ("Required dependencies", check_dependencies),
        ("File structure", check_file_structure),
        (".env configuration", check_env_file),
        ("config.yaml", check_config_file),
        ("Audio devices", check_audio),
        ("STT backend", check_stt_backend),
        ("LLM backend", check_llm_backend),
    ]
    
    results = []
    for name, func in checks:
        results.append(check(name, func))
    
    print(f"\n{BLUE}{'='*60}{RESET}")
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"{GREEN}✓ All checks passed! ({passed}/{total}){RESET}")
        print(f"\n{GREEN}You're ready to run:{RESET}")
        print(f"  python app.py")
        print(f"  # or")
        print(f"  ./run.sh")
        return 0
    else:
        print(f"{YELLOW}⚠ {passed}/{total} checks passed{RESET}")
        print(f"\n{YELLOW}Issues found:{RESET}")
        
        if not results[1]:  # Dependencies
            print(f"\n{YELLOW}Install dependencies:{RESET}")
            print(f"  pip install -r requirements.txt")
        
        if not results[3]:  # .env
            print(f"\n{YELLOW}Create .env file:{RESET}")
            print(f"  cp .env.example .env")
            print(f"  # Edit .env with your API keys")
        
        if not results[5]:  # Audio
            print(f"\n{YELLOW}Audio issues:{RESET}")
            print(f"  - Check microphone is connected")
            print(f"  - Grant microphone permissions")
            print(f"  - Run: python scripts/check_audio.py")
        
        if not results[6]:  # STT
            print(f"\n{YELLOW}Install STT backend:{RESET}")
            print(f"  pip install faster-whisper  # For Whisper")
            print(f"  # or")
            print(f"  pip install vosk  # For Vosk")
            print(f"  python scripts/download_models.py whisper")
        
        if not results[7]:  # LLM
            print(f"\n{YELLOW}Configure LLM:{RESET}")
            print(f"  - Add OPENAI_API_KEY to .env")
            print(f"  # or")
            print(f"  - Set up local LLM and configure LLM_HTTP_URL")
        
        return 1

if __name__ == "__main__":
    sys.exit(main())
