# How to Check Script Execution Logs

## Overview

There are **4 ways** to check logs of scripts running on the server:

1. ✅ **Frontend UI** (Easiest - Recommended)
2. ✅ **Database Query** (Direct access)
3. ✅ **Celery Worker Terminal** (Real-time)
4. ✅ **Backend Logs** (System-level)

---

## Method 1: Frontend UI (Recommended) 🖥️

### Via Scripts Page

**Steps**:
1. Go to: `http://localhost:3000/scripts`
2. Find your script in the table
3. Click the **⬇️ Download icon** (View Logs button)
4. See logs in a modal popup

**Features**:
- ✅ Real-time log updates
- ✅ Shows execution logs
- ✅ Shows error messages
- ✅ Easy to use
- ✅ No technical knowledge needed

**Screenshot Visual**:
```
┌─────────────────────────────────────────────┐
│ Script: my_script.py                        │
│ Actions: ▶️  ⬇️  🗑️                         │
│           ↑                                  │
│       Click here!                           │
└─────────────────────────────────────────────┘

Opens Modal:
┌─────────────────────────────────────────────┐
│ Execution Logs - my_script.py          ✖    │
├─────────────────────────────────────────────┤
│                                             │
│  Starting script...                         │
│  Processing data...                         │
│  Iteration 1/10                             │
│  Iteration 2/10                             │
│  ...                                        │
│  Script completed successfully!             │
│                                             │
└─────────────────────────────────────────────┘
```

---

## Method 2: Database Query 🗄️

### Direct PostgreSQL Query

**Connect to database**:
```bash
psql -U postgres -d dollarclub
```

**View all scripts with logs**:
```sql
SELECT 
    id,
    original_filename,
    status,
    started_at,
    completed_at,
    execution_logs,
    error_message
FROM scripts
ORDER BY started_at DESC;
```

**View specific script logs**:
```sql
SELECT 
    original_filename,
    status,
    execution_logs
FROM scripts
WHERE id = 1;
```

**View only running scripts**:
```sql
SELECT 
    id,
    original_filename,
    started_at,
    execution_logs
FROM scripts
WHERE status = 'RUNNING';
```

**View failed scripts with errors**:
```sql
SELECT 
    id,
    original_filename,
    error_message,
    execution_logs
FROM scripts
WHERE status = 'FAILED'
ORDER BY completed_at DESC
LIMIT 10;
```

---

## Method 3: Celery Worker Terminal (Real-time) 🔴

### Watch Live Execution

When you run the Celery worker, it shows **real-time output** of script execution.

**Start Celery with verbose logging**:
```bash
cd backend
celery -A app.tasks.celery_app worker --loglevel=info --pool=solo
```

**You'll see output like this**:

```
[2025-10-20 10:15:23,456: INFO] Task execute_script[abc-123] received
[2025-10-20 10:15:23,789: INFO] Script 1: Starting script...
[2025-10-20 10:15:24,123: INFO] Script 1: Processing data...
[2025-10-20 10:15:24,456: INFO] Script 1: Iteration 1/10
[2025-10-20 10:15:25,789: INFO] Script 1: Iteration 2/10
[2025-10-20 10:15:27,012: INFO] Script 1: Script completed successfully!
[2025-10-20 10:15:27,345: INFO] Script 1 completed successfully
[2025-10-20 10:15:27,678: INFO] Task execute_script[abc-123] succeeded in 4.2s
```

**Explanation**:
- `Script 1:` prefix = Output from your script
- `Task execute_script[abc-123]` = Celery task info
- Real-time updates as script runs

**Benefits**:
- ✅ Immediate feedback
- ✅ See errors as they happen
- ✅ Debug script issues live
- ✅ No database query needed

---

## Method 4: Backend Application Logs 📝

### Check FastAPI Logs

The backend server also logs script execution events.

**FastAPI Terminal Output**:
```
INFO:     127.0.0.1:50794 - "POST /scripts/1/execute HTTP/1.1" 200 OK
INFO:     Application: Script 1 execution started
INFO:     Application: Task queued: abc-123
```

**For more detailed logs**, run with debug level:
```bash
cd backend
uvicorn main:app --reload --port 8001 --log-level debug
```

---

## Method 5: Script Output Files (Optional)

### Add File Logging to Your Scripts

If you want persistent log files on the server:

**In your script**:
```python
import logging
import sys

# Configure logging to file
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/script.log'),  # File
        logging.StreamHandler(sys.stdout)        # Also to stdout
    ]
)

logger = logging.getLogger(__name__)

logger.info("Script started")
logger.info("Processing data...")
logger.info("Script completed")
```

**Then check the file on server**:
```bash
cat /tmp/script.log
```

Or on Windows:
```powershell
type C:\temp\script.log
```

---

## Comparison: Which Method to Use?

| Method | Best For | Real-time | Easy | Technical |
|--------|----------|-----------|------|-----------|
| **Frontend UI** | General users | Yes | ⭐⭐⭐⭐⭐ | ❌ |
| **Database** | Deep inspection | No | ⭐⭐⭐ | ⭐⭐ |
| **Celery Terminal** | Debugging | Yes | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Backend Logs** | System issues | Yes | ⭐⭐⭐⭐ | ⭐⭐ |
| **File Logs** | Archiving | No | ⭐⭐ | ⭐⭐⭐ |

**Recommendation**: 
- **Users**: Use Frontend UI
- **Developers**: Use Celery Terminal + Frontend UI

---

## Real-time Log Monitoring

### Watch Logs Update Live

**Option A: Frontend UI**
1. Open Scripts page
2. Execute a script
3. Click "View Logs" button
4. **Logs update automatically** as script runs!
5. Database updates every 10 lines

**Option B: Database + Watch Command**

```bash
# Linux/Mac
watch -n 1 "psql -U postgres -d dollarclub -c \"SELECT execution_logs FROM scripts WHERE id=1;\""

# Windows PowerShell
while($true) {
    psql -U postgres -d dollarclub -c "SELECT execution_logs FROM scripts WHERE id=1;"
    Start-Sleep -Seconds 1
    Clear-Host
}
```

**Option C: Celery Terminal** (Best for developers)
- Just watch the Celery worker terminal
- Logs appear in real-time as they're printed

---

## Example: Full Monitoring Session

### Scenario: Execute and Monitor a Script

**Terminal 1: FastAPI Backend**
```bash
cd backend
uvicorn main:app --reload --port 8001
```

**Terminal 2: Celery Worker**
```bash
cd backend
celery -A app.tasks.celery_app worker --loglevel=info --pool=solo
```
**↑ Watch this terminal for real-time logs!**

**Terminal 3: Database Monitor** (Optional)
```bash
psql -U postgres -d dollarclub

-- Query logs
SELECT id, original_filename, status, execution_logs 
FROM scripts 
WHERE status = 'RUNNING';
```

**Browser: Frontend**
```
http://localhost:3000/scripts
- Upload script
- Click Execute
- Click View Logs
- Watch real-time updates!
```

---

## Advanced: Log Streaming API

### Get Logs via API (Optional Enhancement)

Currently, logs are stored in the database and retrieved when you view them. If you want **streaming logs**, you could add:

**Backend Endpoint** (to add):
```python
from fastapi import WebSocket

@router.websocket("/ws/scripts/{script_id}/logs")
async def script_logs_stream(
    websocket: WebSocket,
    script_id: int
):
    await websocket.accept()
    # Stream logs in real-time
    while True:
        script = db.query(Script).filter(Script.id == script_id).first()
        await websocket.send_text(script.execution_logs or "")
        await asyncio.sleep(1)
```

**Frontend** (to add):
```tsx
// WebSocket connection for live logs
const ws = new WebSocket(`ws://localhost:8001/ws/scripts/${scriptId}/logs`)
ws.onmessage = (event) => {
  setLogs(event.data)
}
```

---

## Log Storage Details

### Where Logs Are Stored

**Database**:
- Table: `scripts`
- Column: `execution_logs` (TEXT)
- Updated: Every 10 lines during execution
- Final: Complete logs when script finishes

**Script File**:
- Location: `backend/scripts/{uuid}.py`
- Logs: Captured from stdout/stderr via subprocess

**Format**:
```
Line 1 of output
Line 2 of output
Line 3 of output
...
```

---

## Quick Reference

### View Logs in Frontend
```
1. Go to /scripts
2. Click ⬇️ icon
3. See logs in modal
```

### View Logs in Database
```bash
psql -U postgres -d dollarclub
SELECT execution_logs FROM scripts WHERE id = 1;
```

### View Logs in Celery Terminal
```bash
celery -A app.tasks.celery_app worker --loglevel=info --pool=solo
# Watch terminal output
```

### View Logs via API
```bash
curl http://localhost:8001/scripts/1/status
```

Response:
```json
{
  "script_id": 1,
  "status": "completed",
  "logs": "Starting script...\nProcessing...\nDone!",
  "error_message": null,
  "started_at": "2025-10-20T10:15:23",
  "completed_at": "2025-10-20T10:15:27"
}
```

---

## Troubleshooting

### Logs Not Showing in Frontend

**Cause**: Script hasn't produced output yet

**Solution**:
- Check script is actually running (status = "running")
- Ensure script has `print()` statements
- Logs update every 10 lines (may have delay)

---

### Logs Cut Off or Incomplete

**Cause**: Script still running or crashed

**Solution**:
- Wait for script to complete
- Check status (should be "completed" or "failed")
- If stuck, check Celery worker logs

---

### Can't See Logs in Celery Terminal

**Cause**: Log level too high

**Solution**:
```bash
# Use info level for detailed logs
celery -A app.tasks.celery_app worker --loglevel=info

# Or debug for even more detail
celery -A app.tasks.celery_app worker --loglevel=debug
```

---

## Summary

**Easiest Way**: 
- Frontend UI → Scripts page → Click ⬇️ icon

**Best for Debugging**: 
- Celery worker terminal (real-time output)

**Best for Analysis**: 
- Database queries (historical data)

**All methods work together** - choose based on your needs! 🎯

