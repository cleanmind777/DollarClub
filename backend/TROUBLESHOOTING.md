# Troubleshooting Guide

## Script Logging Issues

### Problem: "Can't see logs from my script"

**Symptom**: Script is running but logs are not appearing in the UI.

**Common Causes & Solutions**:

#### 1. Python Output Buffering

**Problem**: Python buffers `print()` output by default.

**Solution**: Add `sys.stdout.flush()` after each print statement:

```python
import sys

print("My message")
sys.stdout.flush()  # Force output to be visible immediately
```

Or use the `flush=True` parameter:

```python
print("My message", flush=True)
```

#### 2. Script Hasn't Produced Output Yet

**Behavior**: Heartbeat messages appear every 2 seconds even without output.

**What you'll see**:
```
[Status: Script running... 3s elapsed, 0 lines captured]
[Status: Script running... 5s elapsed, 0 lines captured]
```

**Solution**: Wait a bit longer, or check if your script logic is correct.

#### 3. Long Sleep Before First Output

**Problem**: Script sleeps a long time before first print.

**Example**:
```python
import time
time.sleep(60)  # Wait 1 minute
print("Starting...")  # Won't see this for 1 minute
```

**Solution**: Print something before the sleep:
```python
import time
print("Waiting 60 seconds...", flush=True)
time.sleep(60)
print("Starting...", flush=True)
```

#### 4. Script Has Syntax Error

**Check**: Look for error messages in the logs or error message box.

#### 5. Using `input()` or Interactive Functions

**Problem**: Script is waiting for user input (which will never come).

**Solution**: Remove all `input()` calls and hardcode values:
```python
# BAD - Don't use input()
name = input("Enter name: ")

# GOOD - Hardcode or use config
name = "default_user"
```

## Example: Fixed Script

**Before (No output visible):**
```python
import time
count = 0
while True:
    time.sleep(3)
    print(f"Count: {count}")
    count += 1
```

**After (Output visible immediately):**
```python
import time
import sys

print("Starting counter loop...", flush=True)

count = 0
while True:
    time.sleep(3)
    print(f"Count: {count}", flush=True)
    count += 1
```

## Package Issues

### Problem: "Missing Python packages detected"

**Solution**: 
1. Copy the pip install command from the error message
2. Run it in the backend environment:
   ```bash
   cd backend
   # Activate venv if using one
   pip install package-name
   ```
3. Restart Celery worker
4. Try running the script again

### Problem: "TA-Lib installation fails"

**Solution**: TA-Lib requires a C library:

**Windows:**
```bash
# Download TA-Lib from: https://github.com/mrjbq7/ta-lib
# Then: pip install ta-lib
```

**Linux:**
```bash
sudo apt-get install ta-lib
pip install ta-lib
```

**macOS:**
```bash
brew install ta-lib
pip install ta-lib
```

## Script Execution Issues

### Problem: Script immediately fails

**Check**:
1. Error message in the logs
2. Package validation errors
3. Python syntax errors
4. File permissions

### Problem: Script hangs/never completes

**Possible Causes**:
1. Infinite loop (expected for long-running strategies)
2. Waiting for user input (`input()`)
3. Network request timeout
4. Deadlock

**Solution**: Add timeout handling and logging:
```python
import signal
import sys

def timeout_handler(signum, frame):
    print("Operation timed out!", flush=True)
    sys.exit(1)

# Set 30 second timeout for operations
signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(30)

# Your code here
print("Starting operation...", flush=True)
# ... operation ...
signal.alarm(0)  # Cancel timeout
print("Operation completed!", flush=True)
```

### Problem: Script stops without error

**Check**:
1. Script hit the maximum execution time (default: 1 hour)
2. Script was cancelled by user
3. Celery worker crashed (check terminal)

## Celery Worker Issues

### Problem: Scripts don't start

**Symptoms**: Status stays at "uploaded" or "pending"

**Solution**:
1. Check if Celery worker is running:
   ```bash
   # Should see worker process in terminal
   celery -A app.tasks.celery_app worker --loglevel=info --pool=threads --concurrency=1
   ```

2. Restart Celery worker:
   - Press `Ctrl+C` in the Celery terminal
   - Run the command again

### Problem: Celery worker crashes

**Check**:
1. Python errors in worker terminal
2. Out of memory
3. Package conflicts

**Solution**: Restart worker and check logs

## Database Issues

### Problem: "Script not found"

**Solution**: Refresh the page and try again

### Problem: Status not updating

**Solution**:
1. Check if Celery worker is running
2. Refresh the page
3. Check browser console for errors

## Performance Issues

### Problem: Logs update slowly

**Current Behavior**:
- Logs refresh every 1 second for running scripts
- Database updates every 2 seconds (heartbeat)

**To Improve**:
1. Ensure your script uses `flush=True` in prints
2. Don't print too frequently (throttle to 1-2 times per second max)
3. Check network connection

### Problem: Too many logs

**Issue**: Tens of thousands of lines slow down the UI

**Solution**: Throttle your output:
```python
import time

counter = 0
while True:
    counter += 1
    # Only print every 10 iterations
    if counter % 10 == 0:
        print(f"Processed {counter} items", flush=True)
```

## Testing Checklist

When your script isn't working:

- [ ] Added `flush=True` to all print statements
- [ ] No `input()` or interactive functions
- [ ] Tested locally first
- [ ] All required packages installed
- [ ] Celery worker is running
- [ ] Script has a print statement early (to test logging)
- [ ] Checked error messages in UI
- [ ] Checked Celery worker terminal for errors

## Quick Tests

### Test 1: Basic Output
```python
import sys
print("Hello from script!", flush=True)
print("Second line", flush=True)
sys.exit(0)
```

**Expected**: See both lines immediately

### Test 2: Loop with Output
```python
import time
import sys

for i in range(5):
    print(f"Iteration {i}", flush=True)
    time.sleep(2)

print("Done!", flush=True)
```

**Expected**: See each iteration after 2 seconds

### Test 3: Heartbeat Test (Silent Script)
```python
import time
time.sleep(20)  # Sleep without output
print("Finally printing!", flush=True)
```

**Expected**: See heartbeat messages every 2 seconds, then final message

## Still Having Issues?

1. **Check the logs**:
   - Frontend: Browser console (F12)
   - Backend: Terminal where `python main.py` is running
   - Celery: Terminal where Celery worker is running

2. **Enable debug logging**:
   ```python
   # In backend/app/core/config.py
   DEBUG: bool = True
   ```

3. **Test with provided scripts**:
   - `backend/scripts/test_loop_with_output.py`
   - `backend/scripts/test_infinite_loop.py`

4. **Check this guide**: [LOGGING_IMPROVEMENTS.md](LOGGING_IMPROVEMENTS.md)

5. **Check package docs**: [PACKAGE_MANAGEMENT.md](PACKAGE_MANAGEMENT.md)

