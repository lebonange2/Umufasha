#!/usr/bin/env python3
"""Simplified test for Ollama with BrainstormAssistant."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from llm.ollama_client import OllamaClient
from brain.model import BrainstormSession
from brain.organizer import Organizer
from brain.assistant import BrainstormAssistant

print("Testing BrainstormAssistant with simplified prompts...")
print("=" * 70)

# Create client
client = OllamaClient(model="gemma3", base_url="http://localhost:11434")
print(f"✅ Client created for model: {client.model}")

# Create session
session = BrainstormSession(project_name="test")
organizer = Organizer(session)
assistant = BrainstormAssistant(client, organizer)
print(f"✅ Assistant created")

# Test with simple input
print(f"\n🧪 Testing with: 'Build a house'")
try:
    response = assistant.process_user_input("Build a house")
    if response:
        print(f"✅ Got response ({len(response)} chars)")
        print(f"   Preview: {response[:150]}...")
        
        ideas = session.get_active_ideas()
        print(f"✅ Ideas added: {len(ideas)}")
        for idea in ideas:
            print(f"   - {idea.text[:60]}")
    else:
        print(f"❌ No response returned")
        sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n✅ ALL TESTS PASSED!")
