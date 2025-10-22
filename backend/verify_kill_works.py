#!/usr/bin/env python3
"""
Verify that process killing actually works
"""

import subprocess
import time
import psutil
import os

print("🧪 Testing Process Kill Mechanism")
print("=" * 50)

# Create a test script
test_script = """
import time
import sys

print("Test script started", flush=True)
for i in range(100):
    print(f"Iteration {i}", flush=True)
    time.sleep(1)
print("Test script completed", flush=True)
"""

script_file = "test_kill_script.py"
with open(script_file, "w") as f:
    f.write(test_script)

print(f"1. Created test script: {script_file}")

# Start the process
print("2. Starting test process...")
process = subprocess.Popen(
    ["python", script_file],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    bufsize=1
)

print(f"   Process started with PID: {process.pid}")

# Wait a bit
print("3. Waiting 3 seconds...")
time.sleep(3)

# Check if running
print(f"4. Checking process status...")
if process.poll() is None:
    print(f"   ✅ Process {process.pid} is running")
else:
    print(f"   ❌ Process already terminated")
    exit(1)

# Test our kill function
print("5. Testing _kill_process() function...")

from app.tasks.script_execution import _kill_process

try:
    _kill_process(process)
    print("   Kill function executed")
except Exception as e:
    print(f"   ❌ Kill function failed: {e}")
    process.kill()

# Wait for kill to complete
time.sleep(1)

# Verify process is dead
print("6. Verifying process is dead...")
if process.poll() is not None:
    print(f"   ✅ Process {process.pid} is DEAD (return code: {process.poll()})")
else:
    print(f"   ❌ Process {process.pid} is STILL RUNNING!")
    print("   Attempting process.kill()...")
    process.kill()
    time.sleep(1)
    if process.poll() is not None:
        print(f"   ✅ Process killed with process.kill()")
    else:
        print(f"   ❌ FAILED TO KILL PROCESS!")

# Check with psutil
print("7. Verifying with psutil...")
try:
    p = psutil.Process(process.pid)
    if p.is_running():
        print(f"   ❌ psutil says process is STILL RUNNING!")
    else:
        print(f"   ✅ psutil confirms process is dead")
except psutil.NoSuchProcess:
    print(f"   ✅ psutil confirms process doesn't exist")

# Cleanup
print("8. Cleaning up test script...")
try:
    os.remove(script_file)
    print(f"   Removed {script_file}")
except:
    pass

print()
print("=" * 50)
print("✅ TEST COMPLETE!")
print()
print("If you saw '✅ Process is DEAD', the kill function works!")
print("If you saw '❌ STILL RUNNING', there's a problem.")

