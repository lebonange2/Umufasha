#!/usr/bin/env python3
"""Test script to verify local LLM (Ollama) is working."""
import asyncio
import sys
import os

# Add project to path
sys.path.insert(0, os.path.dirname(__file__))

from app.llm.client import LLMClient
from app.core.config import settings

async def test_local_llm():
    """Test the local LLM connection."""
    print("=== Testing Local LLM (Ollama) ===\n")
    
    # Check configuration
    print(f"Provider: {settings.LLM_PROVIDER}")
    print(f"Model: {settings.LLM_MODEL}")
    print(f"Local URL: {getattr(settings, 'LLM_LOCAL_URL', 'http://localhost:11434/v1')}")
    print()
    
    # Create client
    if settings.LLM_PROVIDER.lower() == "local":
        base_url = getattr(settings, 'LLM_LOCAL_URL', 'http://localhost:11434/v1')
        client = LLMClient(
            api_key=None,
            base_url=base_url,
            model=settings.LLM_MODEL,
            provider="local"
        )
    else:
        print(f"⚠️  Warning: LLM_PROVIDER is set to '{settings.LLM_PROVIDER}', not 'local'")
        print("   Set LLM_PROVIDER=local in .env to use local models")
        return False
    
    print(f"Connecting to: {client.base_url}")
    print(f"Using model: {client.model}\n")
    
    # Test connection
    try:
        print("Testing connection...")
        response = await client.complete(
            system="You are a helpful assistant.",
            user="Say 'Hello! Local LLM is working!' if you can respond."
        )
        print(f"✓ Connection successful!")
        print(f"\nResponse:\n{response}\n")
        return True
    except Exception as e:
        print(f"✗ Connection failed: {e}\n")
        print("Troubleshooting:")
        print("  1. Make sure Ollama is running: ollama serve")
        print("  2. Check if model is installed: ollama list")
        print("  3. Pull the model if needed: ollama pull llama3.1")
        print("  4. Test Ollama API: curl http://localhost:11434/api/tags")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_local_llm())
    sys.exit(0 if success else 1)

