# Real-Time Logging Improvements for Infinite Loops

## Problem
Previously, scripts with infinite loops that didn't produce output wouldn't show any logs, making it appear as if nothing was happening.

## Solution

### Backend Changes (`app/tasks/script_execution.py`)

1. **Heartbeat Mechanism**: Added periodic database updates every 2 seconds, even when there's no script output
   - Shows elapsed time and number of lines captured
   - Prevents the appearance of a "frozen" script

2. **Status Messages**: Adds periodic status updates to logs:
   ```
   [Status: Script running... 10s elapsed, 5 lines captured]
   ```

3. **Initial Status**: Shows "Script started, waiting for output..." when script begins

### Frontend Changes (`src/pages/Scripts.tsx`)

1. **Auto-Scroll**: Logs automatically scroll to the bottom when new content arrives
2. **Visual Indicators**: 
   - Yellow status bar showing "RUNNING" with pulsing animation
   - Spinning refresh icon when logs are being updated
3. **Better Empty States**: Shows appropriate messages based on script status

## Testing

Two test scripts are provided:

### 1. Test with Periodic Output
```bash
# Upload: backend/test_infinite_loop.py
# This script prints output every 5 seconds
```

### 2. Test Silent Infinite Loop
```bash
# Upload: backend/test_silent_loop.py
# This script has NO output - tests the heartbeat mechanism
```

## How to Test

1. **Start the backend and Celery**:
   ```bash
   cd backend
   python main.py
   celery -A app.tasks.celery_app worker --loglevel=info --pool=threads --concurrency=1
   ```

2. **Upload a test script** via the frontend

3. **Run the script** and open the logs modal

4. **Observe**:
   - Logs refresh every 1 second (shown in status bar)
   - For silent scripts, you'll see heartbeat messages every 2 seconds
   - Logs auto-scroll to the bottom
   - You can cancel the script anytime using the "Stop Script" button

## Technical Details

- **Heartbeat Interval**: 2 seconds (configurable in code)
- **Frontend Polling**: 1 second
- **Database Commits**: On every output line + heartbeat interval
- **Auto-scroll Delay**: 50ms (to allow DOM update)

## Benefits

1. ✅ **Visibility**: Always know if your script is running
2. ✅ **Debugging**: Easier to debug infinite loops
3. ✅ **Monitoring**: See elapsed time and progress
4. ✅ **Responsiveness**: Cancel works even during long computations
5. ✅ **Real-time**: See logs as they happen, not just at the end

