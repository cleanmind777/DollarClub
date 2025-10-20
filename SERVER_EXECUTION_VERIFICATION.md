# ✅ Server-Side Script Execution - Verification Guide

## Confirmation: Scripts Run on the Server

Your implementation is **correct**. When a user clicks the START button, the script executes **on the server**, not in the browser.

---

## Complete Execution Flow

### 1️⃣ **Frontend Button Click**

**File**: `frontend/src/pages/Scripts.tsx` (Line 139-142)

```tsx
const handleExecute = (script: Script) => {
  if (script.status === 'running') return
  executeMutation.mutate(script.id)  // Triggers mutation
}
```

**Mutation**: (Line 53-63)
```tsx
const executeMutation = useMutation(
  async (scriptId: number) => {
    const response = await api.post(`/scripts/${scriptId}/execute`)
    //                              ↑ Sends HTTP request to server
    return response.data
  }
)
```

---

### 2️⃣ **Backend API Endpoint**

**File**: `backend/app/api/scripts.py` (Line 141-186)

```python
@router.post("/{script_id}/execute")
async def execute_script_endpoint(
    script_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Validates script exists
    # Checks if already running
    # Checks concurrent execution limit
    
    # ⚡ QUEUES CELERY TASK FOR SERVER EXECUTION
    task = execute_script.delay(script_id)  # Line 179
    
    return {
        "message": "Script execution started",
        "task_id": task.id,
        "script_id": script_id
    }
```

**Key Line 179**: `execute_script.delay(script_id)` 
- This queues a background task
- Task runs in Celery worker (separate process)
- Returns immediately to frontend

---

### 3️⃣ **Celery Worker Executes Script on Server**

**File**: `backend/app/tasks/script_execution.py` (Line 53-125)

```python
@celery_app.task(bind=True, name="execute_script")
def execute_script(self, script_id: int):
    # Get script from database
    script = db.query(Script).filter(Script.id == script_id).first()
    
    # ⚡ RUN SCRIPT ON SERVER USING SUBPROCESS
    process = subprocess.Popen(
        [python_executable, script.file_path],  # Line 54-62
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        cwd=os.path.dirname(script.file_path)
    )
    
    # Capture output in real-time
    while True:
        output = process.stdout.readline()
        logs.append(output)
        # Save to database
        script.execution_logs = "\n".join(logs)
        db.commit()
    
    # Update final status
    script.status = ScriptStatus.COMPLETED  # or FAILED
    db.commit()
```

**Key**: `subprocess.Popen(['python', script.file_path])` 
- ✅ Runs Python script **on the server**
- ✅ Captures stdout/stderr
- ✅ Logs saved to database
- ✅ Status updated in real-time

---

## Proof: Server-Side Execution

### Where Scripts Run:

| Component | Location | Purpose |
|-----------|----------|---------|
| Frontend | User's Browser | Only sends HTTP request |
| Backend API | Server (FastAPI) | Receives request, queues task |
| **Celery Worker** | **Server Process** | **Executes Python script** ✅ |
| Script File | Server Disk (`backend/scripts/`) | **Actual script location** ✅ |

### Evidence:

1. **Script saved on server**: `backend/scripts/{uuid}.py`
2. **Subprocess runs on server**: `subprocess.Popen(['python', script.file_path])`
3. **Logs stored in server database**: PostgreSQL
4. **Process runs in Celery worker**: Separate server process

---

## How to Verify

### 1. **Check Script Directory on Server**

```bash
# On your server
cd backend/scripts
ls -la
# You'll see uploaded .py files stored HERE (on server)
```

### 2. **Monitor Celery Worker Logs**

When you start the Celery worker, you'll see:

```bash
cd backend
celery -A app.tasks.celery_app worker --loglevel=info --pool=solo

# When script executes, you'll see:
[INFO] Task execute_script[abc-123] received
[INFO] Script 1: Starting script...
[INFO] Script 1: Processing data...
[INFO] Script 1 completed successfully
[INFO] Task execute_script[abc-123] succeeded in 5.2s
```

This proves the script is **running on the server** in the Celery worker!

### 3. **Check Server Resources**

While script is running:

```bash
# On server - you'll see Python process
ps aux | grep python
# Shows: python /path/to/backend/scripts/{uuid}.py

# Check CPU/memory usage
top
# You'll see the Python process consuming resources ON THE SERVER
```

### 4. **Test with File System Script**

Create a script that writes to the server file system:

```python
# test_server.py
with open('/tmp/server_test.txt', 'w') as f:
    f.write('This file was created on the SERVER!')
print('File written to server!')
```

Upload and execute. Then check on the **server**:

```bash
cat /tmp/server_test.txt
# Output: This file was created on the SERVER!
```

This proves it runs on the server, not the browser! ✅

---

## Requirements for Server Execution

### ✅ Already Configured:

1. **FastAPI Backend** - Receives execute requests
2. **Celery Task** - Queues background execution
3. **subprocess.Popen** - Runs Python on server
4. **Database Tracking** - Stores logs and status

### ⚠️ Required Services:

You need **2 services running**:

#### 1. **FastAPI Server** (Receives requests)
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

#### 2. **Celery Worker** (Executes scripts on server)
```bash
cd backend
celery -A app.tasks.celery_app worker --loglevel=info --pool=solo
```

**Without Celery worker**: 
- Scripts won't execute (task stays queued)
- Status stays "uploaded" 
- No logs captured

**With Celery worker**:
- ✅ Scripts execute on server
- ✅ Real-time log capture
- ✅ Status updates
- ✅ Full control (start/stop/delete)

---

## Quick Test

### Test Script: `hello_server.py`

```python
import platform
import socket
import os

print(f"Running on: {platform.node()}")  # Server hostname
print(f"OS: {platform.system()}")
print(f"IP: {socket.gethostname()}")
print(f"Current directory: {os.getcwd()}")  # Server path
print(f"Script path: {__file__}")  # Server file path
```

**Upload** → **Execute** → **View Logs**

Expected output:
```
Running on: your-server-name
OS: Windows/Linux/Darwin
IP: your-server-ip
Current directory: D:\HSK\code\DollarClub\backend\scripts
Script path: D:\HSK\code\DollarClub\backend\scripts\abc-123.py
```

This clearly shows it's running **on the server**, not the browser! 🎯

---

## Architecture Diagram

```
┌─────────────────┐
│  User Browser   │
│   (Frontend)    │
└────────┬────────┘
         │ HTTP: POST /scripts/123/execute
         │
         ↓
┌─────────────────┐
│  FastAPI Server │ ← Running on SERVER
│   (Backend)     │
└────────┬────────┘
         │ Celery: execute_script.delay(123)
         │
         ↓
┌─────────────────┐
│  Celery Worker  │ ← Running on SERVER
│  (Background)   │
└────────┬────────┘
         │ subprocess.Popen(['python', 'script.py'])
         │
         ↓
┌─────────────────┐
│  Python Process │ ← ⚡ SCRIPT RUNS HERE (SERVER) ⚡
│  (Your Script)  │
└─────────────────┘
         │
         ↓
    Database (logs, status)
```

---

## Summary

✅ **YES, scripts run on the server!**

The implementation is correct:
- Frontend only sends HTTP requests
- Backend queues Celery tasks
- Celery worker executes scripts using subprocess
- Scripts run as Python processes **on the server**
- Logs are captured and stored in database
- Frontend polls for updates

**To use it**:
1. Start FastAPI server
2. **Start Celery worker** (critical!)
3. Upload script via frontend
4. Click START button
5. Script runs **on the server**
6. View real-time logs

**Your scripts execute server-side! 🚀**

