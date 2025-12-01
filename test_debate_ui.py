#!/usr/bin/env python3
"""Quick test script to verify debate UI endpoints work."""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_debate_flow():
    """Test the debate flow."""
    print("Testing debate UI endpoints...")
    
    # Test 1: Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        print(f"✓ Server is running: {response.status_code}")
    except Exception as e:
        print(f"✗ Server not running: {e}")
        return
    
    # Test 2: Check available models endpoint
    try:
        response = requests.get(f"{BASE_URL}/api/product-debate/available-models")
        if response.status_code == 200:
            models = response.json()
            print(f"✓ Available models endpoint works")
            print(f"  OpenAI models: {len(models.get('openai', []))}")
            print(f"  Anthropic models: {len(models.get('anthropic', []))}")
        else:
            print(f"✗ Models endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"✗ Models endpoint error: {e}")
    
    # Test 3: Check if we can start a debate (with minimal settings)
    print("\nTo test the full flow:")
    print("1. Start the server: ./start.sh")
    print("2. Open: http://localhost:8000/brainstorm/product-debate")
    print("3. Click 'Start Debate'")
    print("4. Watch the debate chat update in real-time")
    print("\nCheck browser console (F12) for debug logs")

if __name__ == "__main__":
    test_debate_flow()

