#!/usr/bin/env python3
"""Test script to verify graph loading works correctly."""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import asyncio
from app.graph.connection import get_neo4j_driver, get_neo4j_session
from app.graph.repository import GraphRepository

def test_neo4j_connection():
    """Test if Neo4j is accessible."""
    try:
        driver = get_neo4j_driver()
        driver.verify_connectivity()
        print("✅ Neo4j connection successful")
        return True
    except Exception as e:
        print(f"❌ Neo4j connection failed: {e}")
        print("   Make sure Neo4j is running: docker-compose up -d neo4j")
        return False

def test_create_project():
    """Test creating a project in Neo4j."""
    test_project_id = "test-project-123"
    try:
        node = GraphRepository.create_project(
            project_id=test_project_id,
            title="Test Book",
            genre=None
        )
        print(f"✅ Created test project: {node['id']}")
        return True
    except Exception as e:
        print(f"❌ Failed to create project: {e}")
        return False

def test_get_subgraph():
    """Test getting subgraph."""
    test_project_id = "test-project-123"
    try:
        result = GraphRepository.get_subgraph(project_id=test_project_id, depth=2)
        print(f"✅ Retrieved subgraph: {len(result.get('nodes', []))} nodes, {len(result.get('edges', []))} edges")
        return True
    except Exception as e:
        print(f"❌ Failed to get subgraph: {e}")
        return False

def test_missing_project():
    """Test getting subgraph for non-existent project."""
    test_project_id = "non-existent-project-999"
    try:
        result = GraphRepository.get_subgraph(project_id=test_project_id, depth=2)
        nodes = result.get('nodes', [])
        edges = result.get('edges', [])
        if len(nodes) == 0 and len(edges) == 0:
            print(f"✅ Missing project handled gracefully: empty graph returned")
            return True
        else:
            print(f"❌ Expected empty graph for missing project, got {len(nodes)} nodes")
            return False
    except Exception as e:
        print(f"❌ Failed to handle missing project gracefully: {e}")
        return False

if __name__ == "__main__":
    print("Testing Neo4j Graph Loading...")
    print("=" * 50)
    
    results = []
    
    # Test 1: Connection
    results.append(("Connection", test_neo4j_connection()))
    
    if results[-1][1]:  # Only continue if connection works
        # Test 2: Create project
        results.append(("Create Project", test_create_project()))
        
        # Test 3: Get subgraph
        results.append(("Get Subgraph", test_get_subgraph()))
        
        # Test 4: Missing project
        results.append(("Missing Project", test_missing_project()))
    
    print("=" * 50)
    print("\nTest Results:")
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {name}: {status}")
    
    all_passed = all(result[1] for result in results)
    if all_passed:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed")
        sys.exit(1)

