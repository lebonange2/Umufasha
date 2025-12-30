#!/usr/bin/env python3
"""Check for duplicates in chat log."""
import requests
import json
import sys

BASE_URL = "http://localhost:8000"

# Get the latest project
projects_response = requests.get(f"{BASE_URL}/api/core-devices/projects")
projects = projects_response.json().get("projects", [])

if not projects:
    print("No projects found")
    sys.exit(1)

# Get the most recent project
project = projects[0]
project_id = project["id"]

print(f"Analyzing project: {project_id}")
print()

# Get project details
project_response = requests.get(f"{BASE_URL}/api/core-devices/projects/{project_id}")
project_data = project_response.json()

chat_log = project_data.get("chat_log", [])

print(f"Total messages: {len(chat_log)}")
print()

# Group messages by content and timestamp
messages_by_content = {}
for idx, msg in enumerate(chat_log):
    content = msg.get("content", "")
    timestamp = msg.get("timestamp", "")
    key = f"{content}||{timestamp}"
    
    if key not in messages_by_content:
        messages_by_content[key] = []
    messages_by_content[key].append(idx)

# Find duplicates (same content AND timestamp)
exact_duplicates = {k: v for k, v in messages_by_content.items() if len(v) > 1}

if exact_duplicates:
    print(f"❌ Found {len(exact_duplicates)} exact duplicates (same content AND timestamp):")
    for key, indices in list(exact_duplicates.items())[:5]:
        content, timestamp = key.split("||")
        print(f"\nMessage at indices {indices}:")
        print(f"  Content: {content[:80]}...")
        print(f"  Timestamp: {timestamp}")
        print(f"  Appears: {len(indices)} times")
else:
    print("✅ No exact duplicates found!")

print()

# Also check for same content but different timestamps
content_only = {}
for msg in chat_log:
    content = msg.get("content", "")
    if content not in content_only:
        content_only[content] = []
    content_only[content].append(msg.get("timestamp"))

content_duplicates = {k: v for k, v in content_only.items() if len(v) > 1}

if content_duplicates:
    print(f"⚠️  Found {len(content_duplicates)} messages with same content but different timestamps:")
    for content, timestamps in list(content_duplicates.items())[:5]:
        print(f"\n  '{content[:80]}...'")
        print(f"  Timestamps: {timestamps[:3]}")  # Show first 3
else:
    print("✅ No content duplicates found!")
