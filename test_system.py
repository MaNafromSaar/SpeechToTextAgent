#!/usr/bin/env python3
"""Test script for the containerized STT system."""

import requests
import json
import time

def test_services():
    """Test the STT containerized services."""
    
    print("🧪 Testing STT Containerized System\n")
    
    # Test 1: Check service health
    print("1. Testing service health...")
    
    services = [
        ("Knowledge Base", "http://localhost:8001/health"),
        ("STT Core", "http://localhost:8000/health")
    ]
    
    for name, url in services:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"   ✅ {name}: {response.json()}")
            else:
                print(f"   ❌ {name}: HTTP {response.status_code}")
        except Exception as e:
            print(f"   ❌ {name}: {e}")
    
    print()
    
    # Test 2: Knowledge base operations
    print("2. Testing knowledge base operations...")
    
    try:
        # Add a test entry
        test_entry = {
            "original_text": "Das ist ein test text mit fehlern",
            "processed_text": "Das ist ein Testtext ohne Fehler",
            "format_type": "test_correction",
            "metadata": {"test": True}
        }
        
        response = requests.post("http://localhost:8001/entries", json=test_entry, timeout=10)
        if response.status_code == 200:
            print("   ✅ Knowledge base entry creation")
        else:
            print(f"   ❌ Knowledge base entry creation: {response.status_code}")
        
        # Search test
        search_response = requests.post("http://localhost:8001/search", 
                                      json={"query": "test text", "limit": 5}, 
                                      timeout=10)
        if search_response.status_code == 200:
            results = search_response.json()
            print(f"   ✅ Knowledge base search: Found {len(results.get('results', []))} results")
        else:
            print(f"   ❌ Knowledge base search: {search_response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Knowledge base operations: {e}")
    
    print()
    
    # Test 3: Text processing
    print("3. Testing text processing...")
    
    try:
        test_text = {
            "text": "das ist ein test text mit vielen fehlern und schlechte grammatik",
            "format_type": "test_processing"
        }
        
        response = requests.post("http://localhost:8000/process-text", 
                               json=test_text, timeout=30)
        if response.status_code == 200:
            result = response.json()
            print("   ✅ Text processing successful")
            print(f"      Original: {result['original_text']}")
            print(f"      Processed: {result['processed_text']}")
        else:
            print(f"   ❌ Text processing: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Text processing: {e}")
    
    print()
    
    # Test 4: Service communication
    print("4. Testing inter-service communication...")
    
    try:
        # This should trigger STT core to communicate with knowledge base
        search_response = requests.get("http://localhost:8000/knowledge/search?q=test&limit=5", 
                                     timeout=10)
        if search_response.status_code == 200:
            print("   ✅ Inter-service communication working")
        else:
            print(f"   ❌ Inter-service communication: {search_response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Inter-service communication: {e}")
    
    print("\n🎉 Testing complete!")

if __name__ == "__main__":
    # Wait a bit for services to fully start
    print("⏳ Waiting 5 seconds for services to stabilize...")
    time.sleep(5)
    
    test_services()
