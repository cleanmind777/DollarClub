"""
Direct test of subprocess output capture
This bypasses Celery to test the subprocess logic directly
"""
import subprocess
import sys
import os

# Test script content
test_script = """
import time
print("Line 1")
print("Line 2")
time.sleep(1)
print("Line 3 after sleep")
print("Line 4")
print("Line 5")
"""

# Write test script
script_path = "test_temp_script.py"
with open(script_path, 'w') as f:
    f.write(test_script)

print("Testing subprocess output capture...")
print("=" * 50)

# Set up environment
env = os.environ.copy()
env['PYTHONUNBUFFERED'] = '1'

# Run the script
process = subprocess.Popen(
    [sys.executable, "-u", script_path],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    universal_newlines=True,
    bufsize=0,
    env=env
)

lines_captured = []
print("\nReading output line by line:")
while True:
    line = process.stdout.readline()
    if line:
        line = line.strip()
        print(f"  Captured: {line}")
        lines_captured.append(line)
    
    # Check if process finished
    if process.poll() is not None:
        print(f"\nProcess finished (exit code: {process.poll()})")
        
        # Try to read remaining
        print("Reading remaining output...")
        remaining = process.stdout.read()
        if remaining:
            print(f"Found {len(remaining)} chars in buffer:")
            for rline in remaining.split('\n'):
                rline = rline.strip()
                if rline:
                    print(f"  Remaining: {rline}")
                    lines_captured.append(rline)
        else:
            print("No remaining output in buffer")
        break
    
    # If no line and process still running, continue
    if line == '':
        continue

print("\n" + "=" * 50)
print(f"Total lines captured: {len(lines_captured)}")
print("\nAll captured lines:")
for i, line in enumerate(lines_captured, 1):
    print(f"  {i}. {line}")

# Cleanup
os.remove(script_path)

print("\nExpected: 5 lines (Line 1, 2, 3 after sleep, 4, 5)")
print(f"Actually got: {len(lines_captured)} lines")

if len(lines_captured) == 5:
    print("✓ SUCCESS: All lines captured!")
else:
    print("✗ PROBLEM: Some lines were lost!")

