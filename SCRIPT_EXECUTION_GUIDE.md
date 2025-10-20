# Python Script Execution Guide (Without Docker)

## Overview

Your DollarClub platform can execute uploaded Python scripts **directly on the server** without Docker. This guide explains how it works and how to set it up.

---

## How It Works

### Architecture

```
Frontend → FastAPI → Celery → Python Subprocess → Your Script
                ↓
            PostgreSQL (tracking)
```

1. **User uploads** a Python script via the frontend
2. **FastAPI** saves it to `backend/scripts/` directory
3. **User clicks execute** → FastAPI queues a Celery task
4. **Celery worker** picks up the task and runs the script using `subprocess`
5. **Real-time logs** are captured and stored in the database
6. **Status updates** are tracked (running, completed, failed, cancelled)

### Security Features

✅ **Timeout Protection**: Scripts are killed after `MAX_EXECUTION_TIME` (default: 1 hour)  
✅ **Process Tracking**: All running scripts are tracked and can be cancelled  
✅ **Log Capture**: stdout/stderr are captured in real-time  
✅ **Resource Isolation**: Each script runs in its own subprocess  
✅ **Error Handling**: Crashes and exceptions are logged and reported  

---

## Setup Instructions

### 1. Install Redis (Required for Celery)

#### Windows:
```bash
# Download and install Redis for Windows
# https://github.com/microsoftarchive/redis/releases
# Or use WSL2 with Linux Redis
```

#### Linux:
```bash
sudo apt update
sudo apt install redis-server
sudo systemctl start redis
sudo systemctl enable redis
```

#### macOS:
```bash
brew install redis
brew services start redis
```

### 2. Install Python Dependencies

```bash
cd backend
pip install -r requirements.txt
```

**Key dependency**: `psutil==5.9.6` (for process management)

### 3. Configure Environment Variables

Edit `backend/.env`:

```env
# Redis (for Celery)
REDIS_URL=redis://localhost:6379/0

# Script Execution Settings
MAX_SCRIPT_SIZE=10485760       # 10MB
MAX_EXECUTION_TIME=3600        # 1 hour
MAX_CONCURRENT_SCRIPTS=5       # Max scripts running at once

# Directories
SCRIPTS_DIR=scripts            # Where uploaded scripts are stored
```

### 4. Start the Backend Services

You need **3 terminals**:

#### Terminal 1: FastAPI Server
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

#### Terminal 2: Celery Worker
```bash
cd backend
celery -A app.tasks.celery_app worker --loglevel=info --pool=solo
```

> **Note on Windows**: Use `--pool=solo` on Windows. On Linux/Mac, you can use the default `prefork` pool.

#### Terminal 3: Flower (Optional - Celery Monitoring UI)
```bash
cd backend
celery -A app.tasks.celery_app flower --port=5555
```

Then visit: `http://localhost:5555` to monitor task execution

---

## Script Execution Flow

### 1. Upload Script

**Frontend**:
```tsx
const uploadMutation = useMutation(async (file: File) => {
  const formData = new FormData()
  formData.append('file', file)
  return api.post('/scripts/upload', formData)
})
```

**Backend**:
- Validates file type (`.py`, `.js`, `.ts`)
- Checks file size (max 10MB)
- Saves to `scripts/{uuid}.py`
- Creates database record

### 2. Execute Script

**Backend Endpoint**: `POST /scripts/{script_id}/execute`

**Celery Task**:
```python
# Runs in background worker
@celery_app.task
def execute_script(script_id):
    # 1. Update status to RUNNING
    # 2. Start subprocess: python3 script.py
    # 3. Stream stdout/stderr to database
    # 4. Monitor for timeout
    # 5. Update status to COMPLETED/FAILED
    # 6. Clean up resources
```

### 3. Monitor Execution

**Frontend polls** every 5 seconds:
```tsx
useQuery('scripts', fetchScripts, {
  refetchInterval: 30000  // 30 seconds
})
```

**View Logs**: Click "View Logs" button to see real-time output

### 4. Cancel Script

**Frontend**: Click stop button  
**Backend**: Kills process tree using `psutil`

---

## Example: Test Script

Create `test_script.py`:

```python
import time
import sys

print("Script started!")
print(f"Python version: {sys.version}")

for i in range(10):
    print(f"Iteration {i+1}/10")
    time.sleep(1)

print("Script completed successfully!")
```

**Upload** → **Execute** → **View Logs**

---

## Configuration Options

### Increase Timeout

Edit `backend/.env`:
```env
MAX_EXECUTION_TIME=7200  # 2 hours
```

### Change Python Version

Edit `backend/app/tasks/script_execution.py`:
```python
python_executable = "python3.11"  # or specific version
```

### Use Virtual Environment

For script isolation, create a venv:

```bash
cd backend/scripts
python -m venv script_env
```

Then update `script_execution.py`:
```python
python_executable = os.path.join(settings.SCRIPTS_DIR, "script_env/bin/python")
```

---

## Monitoring & Debugging

### Check Redis Connection

```bash
redis-cli ping
# Should return: PONG
```

### View Celery Logs

```bash
# In the Celery worker terminal, you'll see:
[INFO] Task execute_script[123] received
[INFO] Script 1: Script started!
[INFO] Script 1 completed successfully
[INFO] Task execute_script[123] succeeded
```

### View Script Logs in Database

```sql
SELECT id, original_filename, status, execution_logs, error_message
FROM scripts
WHERE id = 1;
```

### Common Issues

#### Issue: Scripts don't execute
**Solution**: Check Celery worker is running
```bash
celery -A app.tasks.celery_app inspect active
```

#### Issue: "Redis connection refused"
**Solution**: Start Redis server
```bash
# Linux
sudo systemctl start redis

# macOS
brew services start redis
```

#### Issue: Scripts timeout immediately
**Solution**: Check `MAX_EXECUTION_TIME` in `.env`

---

## Security Considerations

### Current Security

✅ File upload validation  
✅ Size limits (10MB)  
✅ Timeout limits (1 hour)  
✅ Process isolation  
✅ Error handling  

### Additional Security (Recommended for Production)

1. **Sandboxing**: Use containers or restricted user accounts
   ```python
   # Linux only: Run as limited user
   import pwd
   def demote(user_uid, user_gid):
       os.setgid(user_gid)
       os.setuid(user_uid)
   
   process = subprocess.Popen(
       [...],
       preexec_fn=lambda: demote(1000, 1000)  # Run as non-privileged user
   )
   ```

2. **Resource Limits**: Limit CPU/memory usage
   ```python
   import resource
   
   def set_limits():
       resource.setrlimit(resource.RLIMIT_CPU, (300, 300))  # 5 min CPU time
       resource.setrlimit(resource.RLIMIT_AS, (512*1024*1024, 512*1024*1024))  # 512MB RAM
   
   process = subprocess.Popen([...], preexec_fn=set_limits)
   ```

3. **Network Isolation**: Block network access if not needed
4. **Code Review**: Review uploaded scripts before execution
5. **File System Limits**: chroot or mount namespaces

---

## Performance Tips

### 1. Use Celery Pooling

For better performance on Linux/Mac:
```bash
celery -A app.tasks.celery_app worker --pool=prefork --concurrency=4
```

### 2. Monitor with Flower

```bash
celery -A app.tasks.celery_app flower
```

Visit `http://localhost:5555` for real-time monitoring

### 3. Database Optimization

Scripts update logs frequently. Consider:
- Batching log updates (currently every 10 lines)
- Using a separate logs table
- Archiving old execution logs

---

## Troubleshooting

### Scripts Stay in "Running" Status Forever

**Cause**: Celery worker crashed  
**Solution**: 
1. Restart Celery worker
2. Manually update script status:
```sql
UPDATE scripts SET status='FAILED', error_message='Worker crashed' 
WHERE status='RUNNING';
```

### Permission Denied Errors

**Cause**: Script directory not writable  
**Solution**:
```bash
chmod 755 backend/scripts
```

### Python Module Not Found

**Cause**: Script uses packages not installed  
**Solution**:
```bash
cd backend
pip install <package-name>
```

---

## Next Steps

- [ ] Set up Redis and Celery
- [ ] Test script execution with simple script
- [ ] Configure timeout and resource limits
- [ ] Set up monitoring with Flower
- [ ] Review security settings for production
- [ ] Consider adding virtual environment per user

**Your scripts now run directly on the server! 🚀**

