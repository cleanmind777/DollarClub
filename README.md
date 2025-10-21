# DollarClub Trading Platform

A robust trading platform where users can authenticate, upload Python trading scripts, and execute them on the server with real-time monitoring and graceful cancellation.

## Table of Contents

- [Architecture](#architecture)
- [Features](#features)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [Environment Variables](#environment-variables)
- [Script Execution & Cancellation](#script-execution--cancellation)
- [Troubleshooting](#troubleshooting)
- [Utility Scripts & Tools](#utility-scripts--tools)
- [Development Tips](#development-tips)
- [Deployment](#deployment)
- [Technical Details](#technical-details)
- [Contributing](#contributing)
- [License](#license)
- [Support](#support)

## Architecture

- **Backend**: FastAPI (API server) + Celery (Background task worker)
- **Frontend**: React with Vite + TailwindCSS
- **Database**: PostgreSQL (shared state for both processes)
- **Message Broker**: Redis (Celery task queue)
- **Script Execution**: subprocess with real-time log streaming
- **Deployment**: Ubuntu VPS with NGINX

### Process Architecture

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   Frontend  │ ──HTTP→ │   FastAPI    │ ──SQL→  │ PostgreSQL  │
│   (React)   │ ←JSON── │  (Process 1) │ ←SQL──  │  (Database) │
└─────────────┘         └──────────────┘         └─────────────┘
                               │                         ↑
                               │ Redis                   │
                               ↓ Queue                   │
                        ┌──────────────┐                 │
                        │    Celery    │ ────────SQL─────┘
                        │  Worker      │
                        │  (Process 2) │
                        └──────────────┘
                               ↓
                        ┌──────────────┐
                        │  subprocess  │
                        │ (User Script)│
                        └──────────────┘
```

**Important**: FastAPI and Celery run in **separate processes** with **separate memory spaces**. They communicate via PostgreSQL (shared state) and Redis (task queue).

## Features

### Authentication
- ✅ Email/Password authentication with JWT tokens
- ✅ Google OAuth integration
- ✅ HTTP-only cookies for secure token storage

### Script Management
- ✅ Upload Python scripts (.py files)
- ✅ View all uploaded scripts with status
- ✅ Execute scripts on server (not locally!)
- ✅ Real-time execution logs streaming
- ✅ **Graceful cancellation** - stop scripts cleanly
- ✅ Delete scripts
- ✅ View logs even for running scripts

### Script Execution Features
- ✅ Asynchronous execution via Celery
- ✅ Real-time log capture (line-by-line)
- ✅ **Cooperative cancellation** (no worker corruption!)
- ✅ Automatic cleanup on worker restart
- ✅ Process isolation and safety
- ✅ Execution time tracking
- ✅ Exit code capture

## Project Structure

```
DollarClub/
├── backend/                           # FastAPI backend
│   ├── app/
│   │   ├── api/                      # API routes
│   │   │   ├── auth.py               # Authentication endpoints
│   │   │   └── scripts.py            # Script management endpoints
│   │   ├── core/                     # Core configuration
│   │   │   ├── config.py             # Settings and environment variables
│   │   │   ├── database.py           # Database connection
│   │   │   └── security.py           # JWT and password hashing
│   │   ├── models/                   # SQLAlchemy models
│   │   │   ├── user.py               # User model
│   │   │   └── script.py             # Script model
│   │   ├── schemas/                  # Pydantic schemas
│   │   │   ├── auth.py               # Auth request/response schemas
│   │   │   ├── user.py               # User schemas
│   │   │   └── script.py             # Script schemas
│   │   ├── services/                 # Business logic services
│   │   │   ├── google_auth.py        # Google OAuth service
│   │   │   └── ibkr_auth.py          # IBKR OAuth service (optional)
│   │   └── tasks/                    # Celery tasks
│   │       ├── celery_app.py         # Celery configuration
│   │       └── script_execution.py   # Script execution task ⭐
│   ├── alembic/                      # Database migrations
│   │   ├── versions/                 # Migration files
│   │   └── env.py                    # Alembic configuration
│   ├── scripts/                      # User uploaded script storage
│   ├── uploads/                      # Temporary upload directory
│   ├── *.bat                         # Windows utility scripts
│   ├── *.py (root level)             # Python utility scripts
│   ├── requirements.txt              # Python dependencies
│   ├── main.py                       # FastAPI application entry point
│   ├── alembic.ini                   # Alembic configuration
│   └── .env                          # Environment variables (create this!)
│
├── frontend/                         # React Vite frontend
│   ├── src/
│   │   ├── pages/                    # Page components
│   │   │   ├── Login.tsx             # Login page
│   │   │   ├── Dashboard.tsx         # Dashboard page
│   │   │   ├── Scripts.tsx           # Scripts management page ⭐
│   │   │   ├── Monitor.tsx           # Monitoring page
│   │   │   └── Settings.tsx          # Settings page
│   │   ├── components/               # Reusable components
│   │   │   ├── Layout.tsx            # Main layout
│   │   │   └── IBKRIntegration.tsx   # IBKR integration
│   │   ├── services/                 # API services
│   │   │   └── auth.tsx              # Auth context and functions
│   │   ├── lib/                      # Library configurations
│   │   │   ├── axios.ts              # Axios instance with interceptors
│   │   │   └── queryClient.ts        # React Query configuration
│   │   ├── routes/                   # Routing
│   │   │   ├── AppRouter.tsx         # Main router
│   │   │   └── ProtectedRoute.tsx    # Route guards
│   │   ├── types/                    # TypeScript types
│   │   │   ├── api.ts                # API types
│   │   │   ├── user.ts               # User types
│   │   │   └── script.ts             # Script types
│   │   ├── utils/                    # Utility functions
│   │   ├── main.tsx                  # React entry point
│   │   └── index.css                 # Global styles (Tailwind)
│   ├── package.json                  # Node dependencies
│   ├── vite.config.ts                # Vite configuration
│   ├── tailwind.config.js            # Tailwind CSS configuration
│   └── tsconfig.json                 # TypeScript configuration
│
├── deployment/                       # Deployment configurations
│   ├── nginx/
│   │   └── nginx.conf                # NGINX configuration
│   ├── systemd/                      # Systemd service files
│   │   ├── dollarclub-backend.service
│   │   ├── dollarclub-celery.service
│   │   └── dollarclub-frontend.service
│   ├── docker-compose.yml            # Docker Compose (optional)
│   ├── deploy.sh                     # Automated deployment script
│   └── env.example                   # Example environment variables
│
├── *.sql                             # SQL setup scripts
├── *.md                              # Documentation files
└── README.md                         # This file
```

### Key Files to Know

- **`backend/app/tasks/script_execution.py`**: Core script execution logic with cooperative cancellation
- **`backend/app/api/scripts.py`**: Script management API endpoints
- **`frontend/src/pages/Scripts.tsx`**: Script management UI with real-time logs
- **`backend/app/tasks/celery_app.py`**: Celery configuration with worker_ready signal
- **`backend/.env`**: Environment variables (you need to create this!)

### Important Directories

- **`backend/scripts/`**: Where uploaded scripts are stored (with UUID filenames)
- **`backend/uploads/`**: Temporary directory for file uploads
- **`backend/alembic/versions/`**: Database migration files
- **`frontend/src/pages/`**: Main application pages

## Quick Start

### Prerequisites
- Python 3.12+
- PostgreSQL
- Redis
- Node.js 18+

### 1. Database Setup
```bash
# Create PostgreSQL database
createdb dollarclub

# Run migrations
cd backend
python -m alembic upgrade head
```

### 2. Backend Setup
```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate
# Or (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment variables
copy env.example .env
# Edit .env with your configuration

# Start FastAPI server
uvicorn main:app --reload --port 8001
```

### 3. Start Redis (for Celery)
```bash
# Windows (via WSL or Docker)
docker run -d -p 6379:6379 redis

# Linux/Mac
redis-server
```

### 4. Start Celery Worker
```bash
# Open NEW terminal
cd backend
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# For Windows (use threads pool - more stable):
celery -A app.tasks.celery_app worker --loglevel=info --pool=threads --concurrency=1

# For Linux/Mac (can use prefork):
celery -A app.tasks.celery_app worker --loglevel=info --pool=prefork --concurrency=1

# Or use the provided script:
# Windows: start_celery_threads.bat
# Linux/Mac: ./start_celery.sh
```

**⚠️ Important**: Use `--pool=threads` on Windows for better stability with script cancellation!

### 5. Frontend Setup
```bash
# Open NEW terminal
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### 6. Access Application
- Frontend: http://localhost:5173
- Backend API: http://localhost:8001
- API Docs: http://localhost:8001/docs

## Environment Variables

### Backend `.env`
```env
# Database
DATABASE_URL=postgresql://user:password@localhost/dollarclub

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Google OAuth (optional)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8001/auth/google/callback

# Script Execution
MAX_EXECUTION_TIME=3600  # 1 hour
UPLOAD_DIR=./uploads
```

### Frontend `.env`
```env
VITE_API_URL=http://localhost:8001
```

## Script Execution & Cancellation

### How It Works

#### 1. Script Upload
- User uploads `.py` file via frontend
- File saved to `backend/uploads/` with UUID filename
- Metadata stored in database

#### 2. Script Execution
```
User clicks "Run" 
    ↓
FastAPI creates Celery task
    ↓
Task stored in Redis queue
    ↓
Celery worker picks up task
    ↓
Worker runs Python script via subprocess
    ↓
stdout/stderr captured line-by-line
    ↓
Logs saved to database in real-time
    ↓
Script completes → status updated
```

#### 3. Script Cancellation (Cooperative)
```
User clicks "Stop"
    ↓
FastAPI updates database: status = CANCELLED
    ↓
Celery task checks database every loop iteration
    ↓
Task detects CANCELLED status
    ↓
Task kills subprocess
    ↓
Task saves final logs
    ↓
Task clears celery_task_id
    ↓
Task returns cleanly ✅
    ↓
Worker ready for next task! ✅
```

### Why Database for Cancellation?

**Problem**: FastAPI and Celery are **separate processes** with **separate memory**.

```
❌ In-Memory Signal (Doesn't Work):
FastAPI: cancelled_scripts.add(123)  # In FastAPI memory
Celery: if 123 in cancelled_scripts  # Checks Celery memory
        └─> Never sees it! Different process!

✅ Database Signal (Works):
FastAPI: script.status = CANCELLED → PostgreSQL
Celery: db.refresh(script) → reads from PostgreSQL
        └─> Sees CANCELLED! Shared state!
```

**Result**: Task detects cancellation within 100ms-1s and exits cleanly without corrupting worker!

### Script Examples

#### Example 1: Simple Script
```python
# upload this as test.py
import time

for i in range(10):
    print(f"Count: {i}")
    time.sleep(1)

print("Done!")
```

#### Example 2: Infinite Loop (Test Cancellation)
```python
import time

count = 0
while True:
    print(f"Running: {count}")
    count += 1
    time.sleep(1)
```

**Test**: Start this script, then click "Stop" - should stop within 1-2 seconds!

## Troubleshooting

### Common Issues

#### Issue: "Script has celery_task_id but doesn't start"
**Cause**: Worker stuck or not running  
**Fix**: 
```bash
# Restart Celery worker
# Ctrl+C to stop, then restart:
celery -A app.tasks.celery_app worker --loglevel=info --pool=threads --concurrency=1

# Or use the batch file (Windows):
start_celery_threads.bat
```

#### Issue: "Can't start new scripts after cancelling"
**Cause**: Worker corrupted (old issue - should be fixed!)  
**Fix**: Already fixed with cooperative cancellation! If still happening:
```bash
# Run diagnostics
python diagnose_scripts.py

# Reset scripts
reset_scripts.bat  # Windows
```

#### Issue: "Only see partial logs"
**Fix**: Already fixed! Using `-u` flag and line-buffered output.

#### Issue: "File not found: scripts/scripts/uuid.py"
**Cause**: Duplicate directory in path  
**Fix**: 
```bash
python fix_script_paths.py
```

#### Issue: "Google OAuth not working"
**Cause**: Missing or incorrect credentials  
**Fix**: 
```bash
# Test configuration
python test_google_oauth.py

# Check these in .env:
# - GOOGLE_CLIENT_ID
# - GOOGLE_CLIENT_SECRET
# - GOOGLE_REDIRECT_URI=http://localhost:8001/auth/google/callback
```

#### Issue: "Database connection failed"
**Cause**: PostgreSQL not running or wrong credentials  
**Fix**: 
```bash
# Run interactive setup
python setup_postgres.py
```

#### Issue: "Scripts stuck in RUNNING status"
**Cause**: Worker crashed while running scripts  
**Fix**: 
```bash
# Diagnose
python diagnose_scripts.py

# Or manually reset
python -c "from app.core.database import SessionLocal; from app.models.script import Script, ScriptStatus; from datetime import datetime; db = SessionLocal(); db.query(Script).filter(Script.status == ScriptStatus.RUNNING).update({'status': ScriptStatus.FAILED, 'error_message': 'Worker restart', 'completed_at': datetime.utcnow()}); db.commit()"
```

### Debug Tips

1. **Check if Celery is running**:
   ```bash
   # Windows
   tasklist | findstr celery
   
   # Linux/Mac
   ps aux | grep celery
   ```

2. **Check Celery logs** for errors:
   ```bash
   # Celery prints to terminal - look for:
   # - "Task succeeded"
   # - "Task exiting cleanly"
   # - Error messages
   ```

3. **Check database script status**:
   ```sql
   SELECT id, name, status, celery_task_id FROM scripts;
   ```

4. **Check Redis connection**:
   ```bash
   redis-cli ping  # Should return "PONG"
   ```

5. **Run diagnostics**:
   ```bash
   python diagnose_scripts.py
   ```

6. **Test cancellation**:
   ```bash
   # Upload infinite loop script
   # Start it
   # Cancel it
   # Try starting another script
   # Should work immediately!
   
   # Or run automated test:
   python test_long_script.py
   ```

## Utility Scripts & Tools

The project includes several utility scripts to help with setup, testing, and troubleshooting.

### Windows Batch Files (`.bat`)

Located in `backend/`:

#### `start_celery_threads.bat` ⭐ **RECOMMENDED**
Starts Celery worker with thread pool (most stable on Windows).
```bash
# From project root:
cd backend
start_celery_threads.bat
```

#### `create_env.bat`
Creates a `.env` file with default configuration.
```bash
cd backend
create_env.bat
```

#### `reset_scripts.bat`
Clears all scripts from database and disk (useful for testing).
```bash
cd backend
reset_scripts.bat
```

#### `apply_celery_fix.bat`
Applies database migrations (runs Alembic).
```bash
cd backend
apply_celery_fix.bat
```

### Python Utility Scripts

Located in `backend/`:

#### `setup_env.py`
Interactive script to create `.env` file with secure random keys.
```bash
cd backend
python setup_env.py
```

#### `setup_postgres.py`
Interactive PostgreSQL database setup and connection tester.
```bash
cd backend
python setup_postgres.py
```
Features:
- Tests PostgreSQL connection
- Creates database
- Generates DATABASE_URL for `.env`
- Auto-updates `.env` file

#### `diagnose_scripts.py`
Diagnoses script execution issues.
```bash
cd backend
python diagnose_scripts.py
```
Shows:
- Scripts in database with status
- Running processes in memory
- Recommendations for stuck scripts

#### `fix_script_paths.py`
Fixes script file paths in database (converts relative to absolute).
```bash
cd backend
python fix_script_paths.py
```
Useful if you see "File not found" errors.

#### `add_celery_column.py`
Adds `celery_task_id` column to scripts table (direct SQL, bypasses Alembic).
```bash
cd backend
python add_celery_column.py
```

### Test Scripts

#### `test_google_oauth.py`
Tests Google OAuth configuration.
```bash
cd backend
python test_google_oauth.py
```
Checks:
- OAuth credentials
- Authorization URL generation
- Redirect URI configuration
- Common issues

#### `test_long_script.py`
Tests long-running script cancellation.
```bash
cd backend
python test_long_script.py
```
Tests:
- Script execution
- Cancellation
- Worker recovery
- Ability to run new scripts after cancellation

#### `verify_kill_works.py`
Verifies that the process kill mechanism works.
```bash
cd backend
python verify_kill_works.py
```

### Deployment Script

#### `deployment/deploy.sh`
Automated deployment script for Ubuntu VPS.
```bash
cd deployment
sudo ./deploy.sh
```
Handles:
- System package installation
- PostgreSQL setup
- Redis configuration
- NGINX configuration
- Systemd service setup
- SSL certificate (Let's Encrypt)

## Development Tips

### Running Backend Tests
```bash
cd backend
pytest
```

### Database Migrations
```bash
# Create new migration
cd backend
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Viewing Logs
- **Backend**: Terminal running `uvicorn`
- **Celery**: Terminal running `celery worker`
- **Frontend**: Browser console + Terminal running `npm run dev`

### Quick Reset (Testing)
If you need a fresh start:
```bash
# 1. Clear all scripts
cd backend
reset_scripts.bat  # Windows
# or
python -c "from app.core.database import SessionLocal; from app.models.script import Script; db = SessionLocal(); db.query(Script).delete(); db.commit()"  # Linux/Mac

# 2. Restart Celery worker
# Ctrl+C then restart with:
celery -A app.tasks.celery_app worker --loglevel=info --pool=threads --concurrency=1
```

## Deployment

See `deployment/` directory for Ubuntu VPS deployment instructions with:
- NGINX reverse proxy
- Systemd services for auto-restart
- HTTPS with Let's Encrypt
- Production configurations

## Technical Details

### Key Design Decisions

1. **Cooperative Cancellation**: No SIGKILL to avoid worker corruption
2. **Database as Shared State**: FastAPI and Celery communicate via PostgreSQL
3. **Thread Pool on Windows**: More stable than solo pool for cancellation
4. **Real-time Log Streaming**: Line-buffered output with immediate DB commits
5. **Unbuffered Python**: `-u` flag ensures logs appear immediately

### Technologies Used
- **FastAPI**: Modern async Python web framework
- **Celery**: Distributed task queue
- **PostgreSQL**: Robust relational database
- **Redis**: In-memory message broker
- **SQLAlchemy**: Python SQL toolkit and ORM
- **Alembic**: Database migration tool
- **React**: Frontend UI library
- **Vite**: Fast frontend build tool
- **TailwindCSS**: Utility-first CSS framework
- **Axios**: HTTP client with interceptors

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

[Add your license here]

## Support

For issues and questions, please open a GitHub issue.
