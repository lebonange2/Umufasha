#!/usr/bin/env python3
"""Test to ensure research phase doesn't loop/duplicate."""
import requests
import time
import json
import sys
import threading

BASE_URL = "http://localhost:8000"

def test_duplicate_prevention():
    """Test that duplicate research execution is prevented."""
    print("=" * 80)
    print("TESTING DUPLICATE RESEARCH EXECUTION PREVENTION")
    print("=" * 80)
    print()
    
    # Step 1: Create project
    print("Step 1: Creating project in research mode...")
    create_response = requests.post(
        f"{BASE_URL}/api/core-devices/projects",
        json={
            "product_idea": "",
            "primary_need": "",
            "research_mode": True,
            "research_scope": "Test duplicate prevention",
            "model": "mock"
        }
    )
    
    if create_response.status_code != 200:
        print(f"❌ Failed to create project: {create_response.status_code}")
        return False
    
    project_id = create_response.json().get("id")
    print(f"✅ Project created: {project_id}")
    print()
    
    # Step 2: Try to execute research TWICE rapidly
    print("Step 2: Attempting to execute research TWICE simultaneously...")
    
    responses = []
    errors = []
    
    def execute_research(index):
        try:
            print(f"  Thread {index}: Sending request...")
            resp = requests.post(
                f"{BASE_URL}/api/core-devices/projects/{project_id}/execute-research"
            )
            responses.append((index, resp.status_code, resp.text))
            print(f"  Thread {index}: Got {resp.status_code}")
        except Exception as e:
            errors.append((index, str(e)))
            print(f"  Thread {index}: ERROR - {e}")
    
    # Launch two threads simultaneously
    thread1 = threading.Thread(target=execute_research, args=(1,))
    thread2 = threading.Thread(target=execute_research, args=(2,))
    
    thread1.start()
    thread2.start()
    
    thread1.join()
    thread2.join()
    
    print()
    print("Results:")
    for index, status, text in responses:
        print(f"  Thread {index}: {status} - {text[:100]}")
    
    # Check that one succeeded (200) and one was rejected (409)
    status_codes = [r[1] for r in responses]
    
    if 200 in status_codes and 409 in status_codes:
        print()
        print("✅ SUCCESS: One execution accepted (200), one rejected (409)")
        print("   Duplicate prevention is working!")
    elif status_codes.count(200) == 2:
        print()
        print("❌ FAILURE: Both executions accepted!")
        print("   Duplicate prevention is NOT working!")
        return False
    else:
        print()
        print(f"⚠️  UNEXPECTED: Status codes were {status_codes}")
        return False
    
    # Step 3: Wait for completion and check chat log
    print()
    print("Step 3: Waiting for research to complete...")
    
    max_attempts = 30
    for attempt in range(max_attempts):
        time.sleep(2)
        status_response = requests.get(
            f"{BASE_URL}/api/core-devices/projects/{project_id}/phase-status"
        )
        
        if status_response.status_code == 200:
            status = status_response.json().get("status")
            if status == "completed":
                print("✅ Research completed!")
                break
            elif status == "failed":
                print(f"❌ Research failed!")
                return False
            else:
                print(f"  Attempt {attempt+1}/{max_attempts}: {status}")
    
    # Step 4: Check chat log for duplicates
    print()
    print("Step 4: Checking chat log for duplicate messages...")
    
    project_response = requests.get(
        f"{BASE_URL}/api/core-devices/projects/{project_id}"
    )
    
    if project_response.status_code != 200:
        print("❌ Failed to get project")
        return False
    
    chat_log = project_response.json().get("chat_log", [])
    
    # Count messages by content
    message_counts = {}
    for msg in chat_log:
        content = msg.get("content", "")
        if content in message_counts:
            message_counts[content] += 1
        else:
            message_counts[content] = 1
    
    # Find duplicates
    duplicates = {k: v for k, v in message_counts.items() if v > 1}
    
    print(f"Total messages: {len(chat_log)}")
    
    if duplicates:
        print(f"❌ Found {len(duplicates)} duplicate message(s):")
        for msg, count in list(duplicates.items())[:5]:  # Show first 5
            print(f"   '{msg[:60]}...' appeared {count} times")
        return False
    else:
        print("✅ No duplicate messages found!")
    
    print()
    print("=" * 80)
    print("✅ ALL TESTS PASSED - No infinite loop!")
    print("=" * 80)
    return True


if __name__ == "__main__":
    print()
    print("🧪 Testing Research Phase Duplicate Prevention")
    print()
    
    try:
        success = test_duplicate_prevention()
        if success:
            print()
            print("🎉 Test completed successfully!")
            sys.exit(0)
        else:
            print()
            print("💥 Test failed!")
            sys.exit(1)
    except Exception as e:
        print()
        print(f"❌ Exception occurred: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
