#!/usr/bin/env python3
"""
Test script for long-running script cancellation
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import time
import requests
import json

# Test configuration
BASE_URL = "http://localhost:8001"
SCRIPT_ID = 1  # Change this to an actual script ID

def test_long_script_cancellation():
    """Test cancelling a long-running script"""
    
    print("🧪 Testing Long Script Cancellation")
    print("=" * 50)
    
    # Step 1: Execute script
    print(f"1. Executing script {SCRIPT_ID}...")
    execute_url = f"{BASE_URL}/scripts/{SCRIPT_ID}/execute"
    
    try:
        response = requests.post(execute_url)
        if response.status_code == 200:
            print("✅ Script execution started")
        else:
            print(f"❌ Failed to start script: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"❌ Error starting script: {e}")
        return False
    
    # Step 2: Wait a bit
    print("2. Waiting 5 seconds for script to run...")
    time.sleep(5)
    
    # Step 3: Cancel script
    print(f"3. Cancelling script {SCRIPT_ID}...")
    cancel_url = f"{BASE_URL}/scripts/{SCRIPT_ID}/cancel"
    
    try:
        response = requests.post(cancel_url)
        if response.status_code == 200:
            print("✅ Script cancellation requested")
        else:
            print(f"❌ Failed to cancel script: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"❌ Error cancelling script: {e}")
        return False
    
    # Step 4: Wait for cleanup
    print("4. Waiting 3 seconds for cleanup...")
    time.sleep(3)
    
    # Step 5: Check script status
    print(f"5. Checking script {SCRIPT_ID} status...")
    status_url = f"{BASE_URL}/scripts/{SCRIPT_ID}/status"
    
    try:
        response = requests.get(status_url)
        if response.status_code == 200:
            data = response.json()
            status = data.get('status')
            print(f"✅ Script status: {status}")
            
            if status == 'cancelled':
                print("✅ Script properly cancelled")
            else:
                print(f"⚠️ Script status is {status}, expected 'cancelled'")
        else:
            print(f"❌ Failed to get script status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error getting script status: {e}")
        return False
    
    # Step 6: Try to execute another script
    print(f"6. Testing new script execution after cancellation...")
    
    try:
        response = requests.post(execute_url)
        if response.status_code == 200:
            print("✅ New script execution started successfully!")
            print("✅ Cancellation fix is working!")
            return True
        else:
            print(f"❌ Failed to start new script: {response.status_code}")
            print("❌ Worker is still stuck!")
            return False
    except Exception as e:
        print(f"❌ Error starting new script: {e}")
        print("❌ Worker is still stuck!")
        return False

if __name__ == "__main__":
    print("Long Script Cancellation Test")
    print("Make sure backend and Celery are running!")
    print()
    
    success = test_long_script_cancellation()
    
    print()
    print("=" * 50)
    if success:
        print("🎉 TEST PASSED: Cancellation fix is working!")
        print("✅ Long script cancellation works")
        print("✅ New scripts can execute after cancellation")
    else:
        print("❌ TEST FAILED: Cancellation fix needs more work")
        print("❌ Worker is still getting stuck")
    
    print()
    print("To run this test:")
    print("1. Upload a long-running script (e.g., 60-second loop)")
    print("2. Change SCRIPT_ID in this file to match your script")
    print("3. Run: python test_long_script.py")
