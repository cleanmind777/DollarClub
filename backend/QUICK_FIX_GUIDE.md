# Quick Fix Guide: Can't See Logs in Loop

## Problem
You're running a script like this:
```python
import time
count = 0
while True:
    time.sleep(3)
    print(f"Count: {count}")
    count += 1
```

And you see logs BEFORE the loop, but NOTHING inside the loop after `time.sleep()`.

## Quick Solution (3 Steps)

### Step 1: Restart Celery Worker ⚡

**This is CRITICAL - must do after ANY code changes!**

```bash
# In your Celery terminal, press Ctrl+C to stop
# Then restart:
cd backend
celery -A app.tasks.celery_app worker --loglevel=info --pool=threads --concurrency=1
```

### Step 2: Upload Test Script 📝

Upload: `backend/scripts/test_sleep_investigation.py`

This script has detailed logging at each step and will show you EXACTLY where it stops.

### Step 3: Check Results 🔍

**What you should see:**
```
Step 1: Script started
Step 2: About to enter loop
Step 3: Entering first iteration
Step 4: Count = 0 (before sleep)
Step 5: About to sleep for 3 seconds...
[Wait 3 seconds]
Step 6: Woke up from sleep!  ← KEY: Do you see this?
Step 7: Count = 0 (after sleep)
Step 8: Script ending
```

## If It Still Doesn't Work

### Option A: Check Celery Terminal

Look for these messages:
```
Script 1: Using wrapper for execution
Script 1: Saved 1 lines to database
Script 1: Heartbeat update (3s elapsed, 1 lines)
```

If you DON'T see "Saved X lines" messages appearing, the wrapper might have an issue.

### Option B: Try Without Wrapper

1. Edit `backend/app/core/config.py`:
   ```python
   USE_SCRIPT_WRAPPER: bool = False  # Change to False
   ```

2. Restart Celery worker

3. Upload this version of your script (with manual flush):
   ```python
   import time
   import sys

   count = 0
   while True:
       time.sleep(3)
       print(f"Count: {count}", flush=True)  # Added flush=True
       sys.stdout.flush()  # Extra flush
       count += 1
   ```

### Option C: Use Diagnostic Scripts

I've created several test scripts in `backend/scripts/`:

1. **test_sleep_investigation.py** - Shows exactly where execution stops
2. **test_no_sleep_loop.py** - Tests loop without sleep
3. **debug_simple_loop.py** - Finite loop with sleep
4. **test_user_loop.py** - Your exact original code

**Try them in this order to isolate the issue.**

## What Was Changed

### Latest Improvements

1. **Better Wrapper** (`script_wrapper.py`):
   - Uses `write_through=True` for zero buffering
   - Double-flushes every print
   - More robust error handling

2. **Configuration Option** (`config.py`):
   - Can enable/disable wrapper for testing
   - `USE_SCRIPT_WRAPPER` flag added

3. **Better Logging** (`script_execution.py`):
   - Shows whether wrapper is being used
   - More detailed debug information

## Expected Behavior

After fixes:

✅ **Before loop**: Logs appear immediately
✅ **Inside loop**: Each print appears within ~1 second
✅ **After sleep**: Output appears after sleep completes
✅ **Heartbeat**: Status messages every 2 seconds if no output

## Common Mistakes

❌ **Forgetting to restart Celery** - Code changes don't apply until restart
❌ **Looking at old logs** - Refresh the page/close and reopen logs modal
❌ **Wrong script** - Make sure you uploaded the latest version
❌ **Wrapper disabled** - Check `USE_SCRIPT_WRAPPER` in config.py

## Still Broken?

Try the full debugging guide: [DEBUGGING_LOGS_ISSUE.md](DEBUGGING_LOGS_ISSUE.md)

Or check:
1. Celery worker terminal - any errors?
2. Browser console (F12) - any JavaScript errors?
3. `test_sleep_investigation.py` - which steps appear?

## Success Indicators

You'll know it's working when:
- ✅ test_sleep_investigation.py shows all 8 steps
- ✅ Your original script shows counts appearing every 3 seconds
- ✅ Celery logs show "Saved X lines to database" messages
- ✅ Heartbeat messages appear in logs every 2 seconds

---

**TL;DR**: 
1. Restart Celery worker
2. Upload test_sleep_investigation.py
3. Check if you see Step 6 ("Woke up from sleep!")
4. If not, check [DEBUGGING_LOGS_ISSUE.md](DEBUGGING_LOGS_ISSUE.md)

