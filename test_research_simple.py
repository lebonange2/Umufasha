#!/usr/bin/env python3
"""Simple test for research phase using requests."""
import os
# MUST set env var before any app imports
os.environ["USE_MOCK_LLM"] = "true"

import requests
import time
import json
import sys

BASE_URL = "http://localhost:8000"

def test_research_phase():
    print("=" * 80)
    print("RESEARCH PHASE API TEST")
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
            "research_scope": "Explore opportunities in consumer electronics for everyday needs",
            "model": "mock"
        }
    )
    
    if create_response.status_code != 200:
        print(f"❌ Failed to create project: {create_response.status_code}")
        print(create_response.text)
        return False
    
    project_data = create_response.json()
    project_id = project_data.get("id")
    
    if not project_id:
        print("❌ No project ID in response")
        print(json.dumps(project_data, indent=2))
        return False
    
    print(f"✅ Project created: {project_id}")
    print()
    
    # Step 2: Execute research
    print("Step 2: Executing research phase...")
    execute_response = requests.post(
        f"{BASE_URL}/api/core-devices/projects/{project_id}/execute-research"
    )
    
    if execute_response.status_code != 200:
        print(f"❌ Failed to execute research: {execute_response.status_code}")
        print(execute_response.text)
        return False
    
    print("✅ Research execution started")
    print()
    
    # Step 3: Poll for completion
    print("Step 3: Waiting for research to complete...")
    max_attempts = 30
    attempt = 0
    
    while attempt < max_attempts:
        attempt += 1
        print(f"  Checking status (attempt {attempt}/{max_attempts})...")
        
        status_response = requests.get(
            f"{BASE_URL}/api/core-devices/projects/{project_id}/phase-status"
        )
        
        if status_response.status_code != 200:
            print(f"  ⚠️  Status check failed: {status_response.status_code}")
            time.sleep(2)
            continue
        
        status_data = status_response.json()
        status = status_data.get("status")
        
        print(f"    Status: {status}")
        
        if status == "completed":
            print("✅ Research phase completed!")
            print()
            print("Status details:")
            print(json.dumps(status_data, indent=2))
            break
        elif status == "failed":
            print("❌ Research phase failed!")
            print(json.dumps(status_data, indent=2))
            return False
        
        time.sleep(2)
    
    if attempt >= max_attempts:
        print("❌ Timeout waiting for research completion")
        return False
    
    # Step 4: Get final project state
    print()
    print("Step 4: Getting final project state...")
    final_response = requests.get(
        f"{BASE_URL}/api/core-devices/projects/{project_id}"
    )
    
    if final_response.status_code != 200:
        print(f"❌ Failed to get project: {final_response.status_code}")
        return False
    
    final_data = final_response.json()
    artifacts = final_data.get("artifacts", {})
    research_artifacts = artifacts.get("research_discovery", {})
    
    print("✅ Research artifacts found:")
    for key in research_artifacts.keys():
        print(f"  - {key}")
    
    print()
    print("=" * 80)
    print("✅ ALL TESTS PASSED!")
    print("=" * 80)
    return True


if __name__ == "__main__":
    print()
    print("🧪 Starting Research Phase Test")
    print()
    
    try:
        success = test_research_phase()
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
