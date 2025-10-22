"""
Test script for infinite loop with periodic output
This demonstrates that logs are now visible in real-time
"""
import time
import sys

print("Starting infinite loop test...")
print("You should see status updates every 2 seconds even without output")
sys.stdout.flush()

counter = 0
while True:
    counter += 1
    
    # Print every 5 seconds to show real-time updates
    if counter % 50 == 0:
        print(f"Loop iteration {counter} - Still running!")
        sys.stdout.flush()
    
    # Small sleep to prevent CPU overload
    time.sleep(0.1)

