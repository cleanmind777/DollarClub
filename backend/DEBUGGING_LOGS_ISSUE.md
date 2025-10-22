# Debugging: Logs Not Showing in Loop

## Current Issue

User reports that:
1. ✅ Logs BEFORE the loop appear
2. ❌ Logs INSIDE the loop (after `time.sleep()`) don't appear
3. ❌ Script seems to hang at `time.sleep()`

## Test Scripts to Use

### Test 1: Sleep Investigation
**File**: `backend/scripts/test_sleep_investigation.py`

This script has detailed logging at each step to identify exactly where it stops:
```python
print("Step 1: Script started")
print("Step 2: About to enter loop")  
print("Step 3: Entering first iteration")
print("Step 4: Count = {count} (before sleep)")
print("Step 5: About to sleep for 3 seconds...")
time.sleep(3)
print("Step 6: Woke up from sleep!")  # Does this appear?
```

**Expected**: See all steps 1-8
**If broken**: See steps 1-5 only

### Test 2: No Sleep Loop
**File**: `backend/scripts/test_no_sleep_loop.py`

Loop without sleep to test if sleep is the issue:
```python
count = 0
while count < 10:
    print(f"Count: {count} (before any sleep)")
    count += 1
```

**Expected**: See all counts 0-9 immediately
**Purpose**: Isolate whether it's a sleep issue or general loop issue

### Test 3: Simple Debug Loop
**File**: `backend/scripts/debug_simple_loop.py`

Finite loop with 2-second sleep:
```python
for i in range(10):
    print(f"INSIDE LOOP - Iteration {i}")
    time.sleep(2)
```

**Expected**: See iterations every 2 seconds
**Purpose**: Test with finite loop instead of infinite

## Configuration Options

### Option 1: Disable Wrapper (for testing)

Edit `backend/app/core/config.py`:
```python
USE_SCRIPT_WRAPPER: bool = False  # Changed from True
```

This runs scripts directly without the wrapper to isolate wrapper issues.

### Option 2: Enable Wrapper (recommended)

```python
USE_SCRIPT_WRAPPER: bool = True  # Default
```

Uses wrapper with forced unbuffering for best output visibility.

## Diagnostic Steps

### Step 1: Restart Celery Worker

**Always do this after any code changes!**

```bash
# Stop current worker (Ctrl+C)
# Then start fresh:
cd backend
celery -A app.tasks.celery_app worker --loglevel=info --pool=threads --concurrency=1
```

### Step 2: Run Test Scripts in Order

1. **test_sleep_investigation.py** - See exactly where it stops
2. **test_no_sleep_loop.py** - Test without sleep
3. **debug_simple_loop.py** - Test with finite loop

### Step 3: Check Celery Worker Terminal

Look for:
- `Script X: Using wrapper for execution` (if wrapper enabled)
- `Script X: Running directly without wrapper` (if wrapper disabled)
- Any Python errors or exceptions
- `Script X: Saved Y lines to database` messages

### Step 4: Check Browser Console

Open browser DevTools (F12) and check for:
- Network errors when fetching logs
- JavaScript errors
- Failed API calls

## Common Issues & Solutions

### Issue 1: Wrapper Script Error

**Symptoms**: Script fails immediately with error

**Solution**: Disable wrapper temporarily:
```python
USE_SCRIPT_WRAPPER: bool = False
```

### Issue 2: Windows Threading Problem

**Symptoms**: Works on Linux/Mac but not Windows

**Problem**: Windows uses threaded readline() which might block

**Solution**: The wrapper should fix this, but if not, we may need to rewrite the Windows output reading logic

### Issue 3: Python Buffering

**Symptoms**: Output appears in batches, not line-by-line

**Test**: Run without wrapper and add `flush=True` manually:
```python
print("Test", flush=True)
```

If this works, the wrapper isn't being applied correctly.

### Issue 4: Database Commit Issue

**Symptoms**: Logs exist but don't show in UI

**Check**: Look at Celery worker logs for "Saved X lines to database"

**Solution**: The heartbeat mechanism should update every 2 seconds

## Debug Logging

### Enable Verbose Logging

Edit `backend/app/core/config.py`:
```python
DEBUG: bool = True  # Changed from False
```

This adds more detailed logging to help diagnose issues.

### Check What the Celery Worker Sees

The Celery worker terminal should show:
```
Script 1: Saved 1 lines to database
Script 1: Heartbeat update (3s elapsed, 1 lines)
Script 1: Saved 2 lines to database
...
```

If you don't see "Saved X lines" messages, the output isn't being captured.

## Expected Behavior

With the wrapper enabled:

1. **Before loop**: Should see initial prints immediately
2. **During loop**: Should see each print within 1 second of execution
3. **After sleep**: Should see output after sleep completes
4. **Heartbeat**: Should see `[Status: ...]` messages every 2 seconds

## Technical Details

### The Wrapper

The wrapper (`script_wrapper.py`) does:

1. Opens stdout with `write_through=True` (no buffering)
2. Replaces `print()` globally with auto-flushing version
3. Executes user script with `exec()`

### The Reading Loop

On Windows, the script execution:

1. Spawns subprocess with stdout=PIPE
2. Creates thread to read from stdout (with timeout)
3. Reads line by line with 100ms timeout
4. Saves each line to database immediately
5. Updates database every 2 seconds (heartbeat)

## Next Steps

1. **Restart Celery** - Always first step
2. **Run test_sleep_investigation.py** - See where it stops
3. **Check Celery terminal** - Look for "Saved X lines" messages
4. **Try without wrapper** - Set USE_SCRIPT_WRAPPER=False
5. **Report findings** - Share which step shows output and which doesn't

## Success Criteria

✅ See "Step 1" through "Step 8" in test_sleep_investigation.py
✅ See all counts in test_no_sleep_loop.py
✅ See iterations appearing every 2 seconds in debug_simple_loop.py
✅ Heartbeat messages appear every 2 seconds
✅ Your original script shows counts every 3 seconds

## Contact

If issue persists after trying all steps:
1. Share the output from `test_sleep_investigation.py` (which steps appear)
2. Share Celery worker terminal output
3. Note whether wrapper is enabled or disabled
4. Share any error messages from browser console

