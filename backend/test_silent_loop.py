"""
Test script for completely silent infinite loop
This demonstrates the heartbeat mechanism - you should see status updates
even though the script produces no output
"""
import time

print("Starting SILENT infinite loop (no output)...")
print("Watch for heartbeat status messages in the logs...")

# Enter infinite loop with NO output
while True:
    time.sleep(1)
    # Silent - no prints, just looping

