#!/usr/bin/env python3
"""
Quick test to check if Ollama is running and accessible.
"""

import asyncio
import httpx


async def test_ollama():
    """Test Ollama connection."""
    
    print("🔍 Testing Ollama Connection...")
    print("=" * 60)
    
    base_url = "http://localhost:11434"
    
    # Test 1: Check if Ollama is running
    print("\n1️⃣  Testing Ollama API endpoint...")
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{base_url}/api/tags")
            if response.status_code == 200:
                print("   ✅ Ollama is running!")
                data = response.json()
                models = data.get("models", [])
                print(f"   📦 Available models: {len(models)}")
                for model in models:
                    print(f"      - {model.get('name')}")
            else:
                print(f"   ❌ Ollama responded with status {response.status_code}")
                return False
    except httpx.ConnectError:
        print("   ❌ Cannot connect to Ollama at http://localhost:11434")
        print("   💡 Make sure Ollama is running: ollama serve")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    # Test 2: Try a simple completion
    print("\n2️⃣  Testing LLM completion with qwen3:30b...")
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            payload = {
                "model": "qwen3:30b",
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Say 'OK' if you can respond."}
                ],
                "stream": False
            }
            
            print("   ⏳ Waiting for response (may take 30-60 seconds on CPU)...")
            response = await client.post(
                f"{base_url}/v1/chat/completions",
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                print(f"   ✅ LLM responded: {content[:100]}")
                return True
            else:
                print(f"   ❌ LLM error: {response.status_code}")
                print(f"   📄 Response: {response.text[:200]}")
                return False
                
    except httpx.TimeoutException:
        print("   ❌ Request timed out after 120 seconds")
        print("   💡 LLM might be too slow on CPU, or model not loaded")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("✅ Ollama is working correctly!")
    return True


if __name__ == "__main__":
    print("\n🧪 Ollama Connection Test\n")
    
    success = asyncio.run(test_ollama())
    
    if success:
        print("\n✅ Research Team should work now!")
        print("If it's still slow, that's expected on CPU (30-60s per LLM call)")
    else:
        print("\n❌ Fix Ollama connection before running research")
        print("\nTo start Ollama:")
        print("  ollama serve")
        print("\nTo pull the model:")
        print("  ollama pull qwen3:30b")
