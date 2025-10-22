# DollarClub Trading Platform

A robust trading platform with script execution, package management, real-time logging, and OAuth integration.

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 16+
- PostgreSQL (optional, SQLite by default)
- Redis (for Celery)

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/macOS)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install common packages for user scripts
install_script_packages.bat  # Windows
./install_script_packages.sh  # Linux/macOS

# Start backend
python main.py
```

### Celery Worker Setup

**In a separate terminal:**

```bash
cd backend
celery -A app.tasks.celery_app worker --loglevel=info --pool=threads --concurrency=1
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The application will be available at:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8001
- **API Docs**: http://localhost:8001/docs

---

## ✨ Features

### 1. Script Execution Engine

Upload and execute trading scripts with:
- ✅ **Real-time logging** - See output as it happens, even in infinite loops
- ✅ **Auto-flushing** - All print statements appear immediately
- ✅ **Heartbeat monitoring** - Status updates every 2 seconds
- ✅ **Auto-scroll logs** - Latest output always visible
- ✅ **Script cancellation** - Stop running scripts anytime
- ✅ **Multiple file types** - Python (.py), JavaScript (.js), TypeScript (.ts)

### 2. Package Management

Automatic dependency detection and validation:
- ✅ **Auto-detection** - Analyzes import statements before execution
- ✅ **Clear error messages** - Shows exact `pip install` commands
- ✅ **40+ pre-installed packages** - pandas, numpy, yfinance, and more
- ✅ **Smart mapping** - Handles cv2→opencv-python, PIL→Pillow, etc.
- ✅ **Security-first** - Auto-install disabled by default

#### Pre-installed Packages

**Data & Analysis:**
- pandas, numpy, scipy
- matplotlib, plotly, seaborn

**Financial APIs:**
- yfinance (Yahoo Finance)
- alpaca-trade-api (Alpaca)
- python-binance (Binance)
- ccxt (Multi-exchange)

**Technical Analysis:**
- pandas-ta
- stockstats

**Machine Learning:**
- scikit-learn
- tensorflow (optional)
- pytorch (optional)

**Utilities:**
- requests, aiohttp
- python-dateutil, pytz
- beautifulsoup4, lxml

### 3. Real-Time Logging System

Advanced logging with heartbeat mechanism:

```python
# Your script - just write normal code!
import time

count = 0
while True:
    time.sleep(3)
    print(f"Count: {count}")  # Appears immediately in UI
    count += 1
```

**Features:**
- Auto-scroll to latest output
- Status updates every 2 seconds (even without output)
- Clear "RUNNING" indicators
- Execution time tracking
- Error message highlighting

### 4. OAuth Integration

- Google OAuth
- IBKR OAuth (Interactive Brokers)

### 5. Modern UI

- Beautiful, responsive design
- Real-time updates
- Modal-based workflows
- Loading indicators
- Error handling with helpful tips

---

## 📦 Package Management

### For Administrators

#### Install Common Packages

```bash
cd backend

# Windows
install_script_packages.bat

# Linux/macOS
chmod +x install_script_packages.sh
./install_script_packages.sh
```

This installs ~40 common trading packages. Takes 5-10 minutes.

#### Configuration

Edit `backend/app/core/config.py`:

```python
# Enable/disable auto-install (use with caution!)
AUTO_INSTALL_PACKAGES: bool = False  # Keep False for security

# Enable/disable wrapper (for debugging)
USE_SCRIPT_WRAPPER: bool = True  # Keep True for best output
```

### For Users

When you upload a script with missing packages, you'll see:

```
Missing Python packages detected!

Your script requires the following packages that are not installed:
alpaca-trade-api, pandas-ta

To install these packages, run:
pip install alpaca-trade-api pandas-ta

Or ask your administrator to install them in the backend environment.
```

Simply share this message with your administrator!

### Writing Scripts

**Best Practices:**

```python
# ✅ GOOD - Works automatically with wrapper
import time

print("Starting trading bot...")

while True:
    time.sleep(5)
    print("Processing tick...")
    # Your trading logic here
```

**No need for:**
- ❌ `flush=True` parameters
- ❌ `sys.stdout.flush()` calls
- ❌ Special output handling

The wrapper handles everything automatically!

---

## 🔧 Real-Time Logging

### How It Works

#### Backend (Automatic)

1. **Wrapper Script** - Patches print() to auto-flush
2. **Heartbeat** - Updates database every 2 seconds
3. **Process Monitoring** - Tracks script status continuously

#### Frontend (Automatic)

1. **Auto-polling** - Fetches logs every 1 second for running scripts
2. **Auto-scroll** - Scrolls to latest output
3. **Visual indicators** - Shows running status with animations

### What You See

**Before loop:**
```
Starting trading bot...
Initializing connection...
```

**During execution:**
```
Processing tick...
[Status: Script running... 5s elapsed, 3 lines captured]
Processing tick...
[Status: Script running... 10s elapsed, 5 lines captured]
Processing tick...
```

**For infinite loops:**
- Heartbeat messages every 2 seconds if no output
- Real-time output as it's produced
- Can cancel anytime

---

## 🐛 Troubleshooting

### Common Issues

#### 1. Can't See Logs in Loop

**Problem:** Logs before loop appear, but nothing inside loop

**Solution:** Restart Celery worker (critical after any code changes!)

```bash
# Press Ctrl+C in Celery terminal
cd backend
celery -A app.tasks.celery_app worker --loglevel=info --pool=threads --concurrency=1
```

#### 2. Missing Packages Error

**Problem:** Script fails with package validation error

**Solution:** Copy the pip install command from the error message:

```bash
cd backend
pip install package-name
# Then restart Celery worker
```

#### 3. Script Hangs

**Possible causes:**
- Using `input()` - Scripts can't accept user input
- Network timeout - Add timeout handling
- Deadlock - Check your code logic

**Solution:** Avoid `input()`, add timeouts, use logging to debug

#### 4. Logs Appear Slowly

**Check:**
- Wrapper enabled? (`USE_SCRIPT_WRAPPER: bool = True`)
- Celery restarted after changes?
- Not printing too frequently? (Throttle to 1-2 times per second max)

#### 5. TA-Lib Won't Install

**Problem:** TA-Lib requires C library

**Solution:**

**Windows:**
```bash
# Download from: https://github.com/mrjbq7/ta-lib
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

### Debug Mode

Enable verbose logging in `backend/app/core/config.py`:

```python
DEBUG: bool = True
```

### Test Scripts

Located in `backend/scripts/`:

- `test_ultra_simple.py` - Basic output test (8 lines)
- `test_sleep_investigation.py` - Detailed step-by-step test
- `test_force_flush_all.py` - Aggressive flushing test
- `test_user_loop.py` - Your infinite loop test
- `debug_simple_loop.py` - Finite loop test

Upload and run these to verify logging works correctly.

---

## 📚 API Documentation

### Script Endpoints

#### Upload Script
```http
POST /scripts/upload
Content-Type: multipart/form-data

file: <script.py>
```

#### List Scripts
```http
GET /scripts/list?skip=0&limit=100
```

#### Get Script Details
```http
GET /scripts/{script_id}
```

#### View Script Content
```http
GET /scripts/{script_id}/content
```

Response:
```json
{
  "script_id": 1,
  "filename": "my_strategy.py",
  "content": "import pandas as pd\n..."
}
```

#### Download Script
```http
GET /scripts/{script_id}/download
```

Returns file for download.

#### Execute Script
```http
POST /scripts/{script_id}/execute
```

Response:
```json
{
  "message": "Script execution started",
  "task_id": "abc-123",
  "script_id": 1
}
```

#### Get Execution Status
```http
GET /scripts/{script_id}/status
```

Response:
```json
{
  "script_id": 1,
  "status": "running",
  "logs": "Step 1: Started\nStep 2: Processing...",
  "error_message": null,
  "started_at": "2025-10-22T10:00:00",
  "completed_at": null
}
```

#### Cancel Script
```http
POST /scripts/{script_id}/cancel
```

#### Delete Script
```http
DELETE /scripts/{script_id}
```

---

## 🏗️ Architecture

### Backend Stack

- **Framework:** FastAPI
- **Database:** SQLite (default) / PostgreSQL (production)
- **Task Queue:** Celery + Redis
- **Authentication:** JWT tokens + OAuth
- **Process Management:** psutil

### Frontend Stack

- **Framework:** React + TypeScript
- **Build Tool:** Vite
- **State Management:** React Query
- **Styling:** Tailwind CSS
- **HTTP Client:** Axios

### Key Components

```
backend/
├── app/
│   ├── api/              # API endpoints
│   ├── core/             # Config, database, security
│   ├── models/           # SQLAlchemy models
│   ├── schemas/          # Pydantic schemas
│   ├── services/         # Business logic
│   └── tasks/            # Celery tasks
│       ├── celery_app.py
│       ├── script_execution.py  # Main execution logic
│       └── script_wrapper.py    # Auto-flush wrapper
├── scripts/              # User-uploaded scripts
└── uploads/              # Uploaded files

frontend/
├── src/
│   ├── components/       # Reusable components
│   │   ├── LoadingModal.tsx
│   │   └── ScriptViewModal.tsx
│   ├── pages/            # Page components
│   │   └── Scripts.tsx   # Main scripts page
│   ├── services/         # API clients
│   └── types/            # TypeScript types
```

---

## 🔒 Security

### Authentication

- JWT tokens stored in HTTP-only cookies
- Token refresh mechanism
- OAuth integration (Google, IBKR)

### Script Execution

- Isolated subprocess execution
- Process timeout (1 hour default)
- Resource limits
- No privileged operations
- Package validation before execution

### Package Management

- Auto-install **disabled by default**
- Standard library filtering
- Known package mappings
- Admin-controlled installation

### CORS

Configured origins in `backend/app/core/config.py`:

```python
CORS_ORIGINS: list = [
    "http://localhost:3000",
    "http://localhost:3001", 
    "http://localhost:5173"
]
```

---

## 🚢 Deployment

### Environment Variables

Create `.env` in backend/:

```bash
# Application
APP_NAME=DollarClub Trading Platform
DEBUG=false
SECRET_KEY=your-secret-key-change-in-production

# Database
DATABASE_URL=postgresql://user:password@localhost/dollarclub

# Redis
REDIS_URL=redis://localhost:6379/0

# Google OAuth
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8001/auth/google/callback

# IBKR OAuth
IBKR_CLIENT_ID=your-ibkr-client-id
IBKR_CLIENT_SECRET=your-ibkr-secret

# Script Settings
MAX_SCRIPT_SIZE=10485760  # 10MB
MAX_EXECUTION_TIME=3600    # 1 hour
MAX_CONCURRENT_SCRIPTS=5

# Package Management
AUTO_INSTALL_PACKAGES=false
USE_SCRIPT_WRAPPER=true

# CORS
CORS_ORIGINS=["http://localhost:3000"]
```

### Production Checklist

- [ ] Set `DEBUG=false`
- [ ] Use PostgreSQL instead of SQLite
- [ ] Set strong `SECRET_KEY`
- [ ] Configure OAuth credentials
- [ ] Set up proper CORS origins
- [ ] Enable HTTPS
- [ ] Set up monitoring
- [ ] Configure log rotation
- [ ] Set resource limits
- [ ] Regular backups
- [ ] Keep packages updated

### Docker Deployment

```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

---

## 🧪 Testing

### Run Backend Tests

```bash
cd backend
python -m pytest
```

### Test Script Execution

```bash
cd backend
python test_subprocess_directly.py
python test_with_wrapper.py
```

### Test Package Detection

Upload test scripts from `backend/scripts/`:
- All should execute correctly
- Check logs appear in real-time
- Verify package errors show helpful messages

---

## 📖 Additional Documentation

- **[PACKAGE_MANAGEMENT.md](backend/PACKAGE_MANAGEMENT.md)** - Full package management guide
- **[PACKAGE_SETUP_QUICKSTART.md](backend/PACKAGE_SETUP_QUICKSTART.md)** - 5-minute setup guide
- **[LOGGING_IMPROVEMENTS.md](backend/LOGGING_IMPROVEMENTS.md)** - Real-time logging details
- **[TROUBLESHOOTING.md](backend/TROUBLESHOOTING.md)** - Comprehensive troubleshooting
- **[DEBUGGING_LOGS_ISSUE.md](backend/DEBUGGING_LOGS_ISSUE.md)** - Debugging guide
- **[QUICK_FIX_GUIDE.md](backend/QUICK_FIX_GUIDE.md)** - Common fixes

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

---

## 📝 License

[Your License Here]

---

## 🆘 Support

### Getting Help

1. **Check logs:**
   - Celery terminal for backend issues
   - Browser console (F12) for frontend issues
   - Script execution logs in UI

2. **Review documentation:**
   - Start with QUICK_FIX_GUIDE.md
   - Check TROUBLESHOOTING.md
   - Read relevant feature docs

3. **Test with provided scripts:**
   - Run test scripts to isolate issues
   - Compare expected vs actual behavior

### Common Commands

```bash
# Restart Celery (after any backend changes)
cd backend
celery -A app.tasks.celery_app worker --loglevel=info --pool=threads --concurrency=1

# Install package for user script
cd backend
pip install package-name
# Then restart Celery!

# Check installed packages
pip list

# View real-time logs
# Just open logs modal in UI - auto-refreshes every 1s

# Cancel running script
# Click "Stop Script" button in logs modal
```

---

## 🎯 Roadmap

### Current Features
- ✅ Script upload and execution
- ✅ Real-time logging with heartbeat
- ✅ Package management
- ✅ View and download scripts
- ✅ OAuth integration
- ✅ Script cancellation

### Planned Features
- [ ] Script scheduling (cron-like)
- [ ] Script versioning
- [ ] Collaborative editing
- [ ] Resource usage metrics
- [ ] Script marketplace
- [ ] Backtesting framework
- [ ] Paper trading integration
- [ ] Live trading with risk controls

---

## 💡 Tips & Best Practices

### For Users

1. **Test locally first** - Debug on your machine before uploading
2. **Add logging** - Use print statements to track progress
3. **Handle errors** - Add try/except blocks
4. **Document dependencies** - List required packages in comments
5. **Avoid infinite loops** - Unless intentional for trading bots
6. **Check logs regularly** - Monitor your scripts

### For Administrators

1. **Keep Celery running** - Essential for script execution
2. **Restart after changes** - Celery doesn't hot-reload
3. **Monitor resources** - Check CPU/memory usage
4. **Regular package updates** - Security and features
5. **Backup database** - Protect user data and scripts
6. **Review logs** - Check for frequently requested packages

---

## 🌟 Highlights

### What Makes This Special

1. **True Real-Time Logging**
   - See output immediately, even in infinite loops
   - No more waiting for scripts to complete
   - Perfect for long-running trading algorithms

2. **Intelligent Package Management**
   - Know instantly if packages are missing
   - Get exact installation commands
   - No surprises during execution

3. **User-Friendly**
   - Clear error messages
   - Helpful tooltips
   - Auto-scroll logs
   - Loading indicators

4. **Developer-Friendly**
   - Clean architecture
   - Comprehensive documentation
   - Easy to extend
   - Well-tested

---

---

## 📋 Detailed Feature Documentation

### Script Execution Deep Dive

#### How Scripts Are Executed

1. **Upload** - File saved to `backend/scripts/` with UUID filename
2. **Validation** - Package dependencies analyzed via AST parsing
3. **Execution** - Celery task spawns subprocess through wrapper
4. **Monitoring** - Logs captured line-by-line + heartbeat every 2s
5. **Completion** - Final output captured, status updated

#### Script Wrapper

Located at `backend/app/tasks/script_wrapper.py`, the wrapper:

```python
# Patches stdout for unbuffered output
sys.stdout = io.TextIOWrapper(
    os.fdopen(sys.stdout.fileno(), 'wb', 0),
    write_through=True  # Key: bypasses all buffering
)

# Patches print() globally
def flushed_print(*args, **kwargs):
    kwargs.setdefault('flush', True)
    original_print(*args, **kwargs)
    sys.stdout.flush()

builtins.print = flushed_print
```

**Result:** Users don't need to add `flush=True` - it's automatic!

#### Heartbeat Mechanism

For scripts with no output:

```python
# Every 2 seconds, adds status message:
[Status: Script running... 5s elapsed, 3 lines captured]
[Status: Script running... 7s elapsed, 3 lines captured]
```

This ensures:
- ✅ You always know the script is running
- ✅ Can monitor long-running processes
- ✅ See elapsed time and progress
- ✅ Cancel works even without output

#### Cancellation Flow

**User clicks "Stop Script":**

1. Frontend sends `POST /scripts/{id}/cancel`
2. FastAPI sets `status = CANCELLED` in database
3. Celery task checks database every loop iteration
4. Detects `CANCELLED` status
5. Kills subprocess gracefully
6. Saves logs and exits cleanly
7. Worker ready for next task immediately

**No worker corruption, no restart needed!**

---

## 🎨 UI Features

### Scripts Page

**Upload Area:**
- Drag & drop support
- File type validation (.py, .js, .ts)
- Size limit (10MB)
- Visual feedback

**Scripts Table:**
- Status indicators with icons
- File size formatting
- Action buttons:
  - ▶️ **Run** - Execute script
  - ⏹️ **Stop** - Cancel running script
  - 👁️ **View** - View script code
  - ⬇️ **Download** - Download script file
  - 📄 **Logs** - View execution logs
  - 🗑️ **Delete** - Remove script

**Modals:**
- **Loading Modal** - Shows during async operations
- **Script View Modal** - Code viewer with syntax detection and copy/download
- **Logs Modal** - Real-time logs with auto-scroll and status indicators

### Dashboard

- Quick stats overview
- Recent activity
- System status

### Settings

- User profile management
- OAuth connections
- Preferences

---

## 🔧 Configuration Reference

### Backend Config (`backend/app/core/config.py`)

```python
class Settings(BaseSettings):
    # Application
    APP_NAME: str = "DollarClub Trading Platform"
    DEBUG: bool = False
    SECRET_KEY: str = "your-secret-key"
    
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost/dollarclub"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8001/auth/google/callback"
    
    IBKR_CLIENT_ID: str = ""
    IBKR_CLIENT_SECRET: str = ""
    IBKR_REDIRECT_URI: str = "http://localhost:8000/auth/ibkr/connect"
    
    # Script Execution
    MAX_SCRIPT_SIZE: int = 10 * 1024 * 1024  # 10MB
    MAX_EXECUTION_TIME: int = 3600  # 1 hour
    MAX_CONCURRENT_SCRIPTS: int = 5
    
    # Package Management
    AUTO_INSTALL_PACKAGES: bool = False  # Security: disabled by default
    
    # Script Execution Options
    USE_SCRIPT_WRAPPER: bool = True  # Enable auto-flush wrapper
    
    # File Storage
    SCRIPTS_DIR: str = "scripts"
    UPLOAD_DIR: str = "uploads"
    
    # CORS
    CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:5173"
    ]
```

### Frontend Config

**Vite Config (`frontend/vite.config.ts`):**

```typescript
export default defineConfig({
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8001',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  }
})
```

**Note:** The proxy means:
- Browser requests: `http://localhost:3000/api/...`
- Proxied to: `http://localhost:8001/...`
- No CORS errors during development!

**Environment Variables (`.env`):**

```bash
VITE_API_URL=http://localhost:8001
```

---

## 🧩 Technology Stack Details

### Backend Technologies

| Technology | Purpose | Version |
|------------|---------|---------|
| FastAPI | Web framework | 0.104+ |
| Celery | Task queue | 5.3+ |
| Redis | Message broker | 7.0+ |
| SQLAlchemy | ORM | 2.0+ |
| Pydantic | Validation | 2.0+ |
| psutil | Process management | 5.9+ |
| aiofiles | Async file I/O | 23.0+ |

### Frontend Technologies

| Technology | Purpose | Version |
|------------|---------|---------|
| React | UI framework | 18+ |
| TypeScript | Type safety | 5+ |
| Vite | Build tool | 4+ |
| Tailwind CSS | Styling | 3+ |
| React Query | State management | 3+ |
| Axios | HTTP client | 1+ |
| Lucide React | Icons | Latest |

---

## 🔐 Security Considerations

### Authentication Security

- ✅ Passwords hashed with bcrypt
- ✅ JWT tokens in HTTP-only cookies (not localStorage)
- ✅ Token expiration and refresh
- ✅ CSRF protection via SameSite cookies

### Script Execution Security

- ✅ Subprocess isolation
- ✅ No shell=True (prevents injection)
- ✅ Timeout enforcement
- ✅ File size limits
- ✅ File type validation
- ✅ User-specific script isolation
- ⚠️ Scripts run with backend's privileges (TODO: sandboxing)

### Package Security

- ✅ Auto-install disabled by default
- ✅ Package validation before execution
- ✅ Only installs from PyPI
- ⚠️ No package whitelisting yet
- ⚠️ No version pinning enforcement

### Future Security Enhancements

- [ ] Docker container per script execution
- [ ] Resource limits (CPU, memory, network)
- [ ] Package whitelisting
- [ ] User-specific virtual environments
- [ ] Audit logging
- [ ] Rate limiting

---

## 📊 Monitoring & Observability

### Logs

**Backend Logs:**
- FastAPI access logs (stdout)
- Application logs (configured in main.py)
- Celery worker logs (terminal)

**Script Execution Logs:**
- Stored in database (`script.execution_logs`)
- Visible in UI in real-time
- Includes heartbeat messages
- Shows errors prominently

### Metrics to Monitor

- Scripts per user
- Execution time distribution
- Failure rates
- Package validation failures
- Celery queue length
- Database connections

### Health Checks

```bash
# Backend health
curl http://localhost:8001/health

# Check Celery worker
celery -A app.tasks.celery_app inspect active

# Check Redis
redis-cli ping
```

---

## 🧪 Testing Guide

### Unit Tests

```bash
cd backend
python -m pytest tests/ -v
```

### Integration Tests

```bash
# Test full flow
python -m pytest tests/integration/ -v
```

### Manual Testing

**Test Scripts in `backend/scripts/`:**

| Script | Purpose | Expected Result |
|--------|---------|-----------------|
| `test_ultra_simple.py` | 8 simple prints | All 8 lines (A-H) |
| `test_force_flush_all.py` | Prints with sleep & flush | All 6 lines |
| `test_sleep_investigation.py` | Detailed step test | All 8 steps |
| `test_user_loop.py` | Infinite loop | Counts every 3s |
| `test_missing_package.py` | Package validation | Success or clear error |
| `test_alpaca_required.py` | Missing package test | Clear error with pip command |

**Testing Checklist:**

- [ ] Upload script succeeds
- [ ] Script appears in list
- [ ] Execute starts script (status → running)
- [ ] Logs appear in real-time
- [ ] Heartbeat messages show up
- [ ] Can view script code
- [ ] Can download script
- [ ] Can cancel running script
- [ ] Cancelled scripts clean up properly
- [ ] Can delete finished scripts
- [ ] Package errors show helpful messages

---

## 🚀 Performance Optimization

### Backend

- Use connection pooling for database
- Configure Celery concurrency based on CPU
- Use Redis for caching
- Optimize database queries
- Index frequently queried fields

### Frontend

- React Query caching (30s stale time)
- Debounced log updates
- Lazy loading for large lists
- Code splitting
- Optimized bundle size

### Script Execution

- Process pooling (future enhancement)
- Resource limits per script
- Throttled log updates
- Efficient database commits

---

## 🌐 Deployment Guide

### Development

```bash
# Terminal 1 - Backend
cd backend
python main.py

# Terminal 2 - Celery
cd backend
celery -A app.tasks.celery_app worker --loglevel=info --pool=threads --concurrency=1

# Terminal 3 - Frontend
cd frontend
npm run dev
```

### Production with Docker

```bash
# Build
docker-compose build

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend
docker-compose logs -f celery
docker-compose logs -f frontend

# Stop
docker-compose down
```

### Manual Production Setup

See `deployment/` directory for:
- NGINX configuration
- Systemd service files
- Environment templates
- SSL setup

---

## 🎓 Learning Resources

### Understanding the Codebase

1. **Start here:** `PACKAGE_SETUP_QUICKSTART.md` - Get running in 5 minutes
2. **Script execution:** `LOGGING_IMPROVEMENTS.md` - How real-time logging works
3. **Package system:** `PACKAGE_MANAGEMENT.md` - Dependency management
4. **Debugging:** `TROUBLESHOOTING.md` - Fix common issues
5. **Quick fixes:** `QUICK_FIX_GUIDE.md` - Fast solutions

### Key Concepts

**Celery Tasks:**
- Tasks run in separate process
- Use database for shared state
- No in-memory communication with FastAPI

**Script Wrapper:**
- Intercepts all print() calls
- Forces immediate flushing
- Makes logging "just work"

**Package Validation:**
- AST parsing (safe, no execution)
- Detects all imports
- Maps import names to package names
- Validates before execution

---

## 🤖 API Integration Examples

### Python Client

```python
import requests

BASE_URL = "http://localhost:8001"

# Login
response = requests.post(f"{BASE_URL}/auth/login", json={
    "username": "user@example.com",
    "password": "password"
})
cookies = response.cookies

# Upload script
with open("my_script.py", "rb") as f:
    response = requests.post(
        f"{BASE_URL}/scripts/upload",
        files={"file": f},
        cookies=cookies
    )
    script_id = response.json()["id"]

# Execute script
response = requests.post(
    f"{BASE_URL}/scripts/{script_id}/execute",
    cookies=cookies
)
task_id = response.json()["task_id"]

# Check status
response = requests.get(
    f"{BASE_URL}/scripts/{script_id}/status",
    cookies=cookies
)
print(response.json()["logs"])
```

### JavaScript Client

```javascript
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8001',
  withCredentials: true
});

// Login
await api.post('/auth/login', {
  username: 'user@example.com',
  password: 'password'
});

// Upload script
const formData = new FormData();
formData.append('file', file);
const { data: script } = await api.post('/scripts/upload', formData);

// Execute
const { data: task } = await api.post(`/scripts/${script.id}/execute`);

// Poll for logs
const interval = setInterval(async () => {
  const { data: status } = await api.get(`/scripts/${script.id}/status`);
  console.log(status.logs);
  
  if (status.status !== 'running') {
    clearInterval(interval);
  }
}, 1000);
```

---

## 📈 Monitoring Dashboard

### Metrics to Track

**System Metrics:**
- CPU usage
- Memory usage
- Disk space
- Network I/O

**Application Metrics:**
- Active users
- Scripts uploaded per day
- Scripts executed per hour
- Average execution time
- Success/failure rates
- Most used packages

**Celery Metrics:**
- Queue length
- Worker status
- Task completion rate
- Failed tasks

### Setting Up Monitoring

**Celery Flower (Recommended):**

```bash
pip install flower
celery -A app.tasks.celery_app flower --port=5555
```

Access at: http://localhost:5555

**Basic Monitoring Script:**

```bash
# Check queue size
celery -A app.tasks.celery_app inspect active

# Check registered tasks
celery -A app.tasks.celery_app inspect registered

# Worker stats
celery -A app.tasks.celery_app inspect stats
```

---

## 🔄 Update & Maintenance

### Updating Packages

```bash
# Update backend packages
cd backend
pip install --upgrade -r requirements.txt
pip install --upgrade -r requirements_scripts.txt

# Update frontend packages
cd frontend
npm update

# Restart services
# - Stop Celery (Ctrl+C) and restart
# - Restart backend (Ctrl+C and restart)
# - Frontend auto-reloads
```

### Database Migrations

```bash
cd backend

# Create migration
alembic revision --autogenerate -m "description"

# Apply migration
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Backup

```bash
# SQLite backup
cp backend/dollarclub.db backend/dollarclub.db.backup

# PostgreSQL backup
pg_dump dollarclub > backup.sql

# Restore
psql dollarclub < backup.sql
```

---

## 🐞 Known Issues & Workarounds

### Issue: Logs Missing After Sleep (Windows)

**Status:** Under investigation

**Workaround:** Add explicit flush in scripts:
```python
import sys
print("Message", flush=True)
sys.stdout.flush()
```

**Test scripts available** to help diagnose.

### Issue: TA-Lib Installation Fails

**Workaround:** 
1. Comment out ta-lib in `requirements_scripts.txt`
2. Install TA-Lib C library manually
3. Then `pip install ta-lib`

### Issue: Celery Worker Not Picking Up Tasks

**Solution:** Restart Celery worker, ensure Redis is running

```bash
# Check Redis
redis-cli ping  # Should return PONG

# Restart Celery
cd backend
celery -A app.tasks.celery_app worker --loglevel=info --pool=threads --concurrency=1
```

---

## 📞 Contact & Support

### Documentation

- **Quick Start:** This README
- **Package Management:** [PACKAGE_SETUP_QUICKSTART.md](backend/PACKAGE_SETUP_QUICKSTART.md)
- **Logging:** [LOGGING_IMPROVEMENTS.md](backend/LOGGING_IMPROVEMENTS.md)
- **Troubleshooting:** [TROUBLESHOOTING.md](backend/TROUBLESHOOTING.md)
- **Debug Guide:** [DEBUGGING_LOGS_ISSUE.md](backend/DEBUGGING_LOGS_ISSUE.md)

### Getting Help

1. Check documentation (see links above)
2. Run test scripts to isolate issues
3. Check Celery terminal for error messages
4. Review browser console for frontend errors
5. Check GitHub issues
6. Contact maintainers

---

## 🏆 Credits

Built with modern tools and best practices:
- FastAPI for high-performance async API
- Celery for reliable task execution
- React + TypeScript for type-safe UI
- Tailwind for beautiful styling
- And many more amazing open-source projects

---

## 📄 License

[Your License Here]

---

**Built with ❤️ for traders and developers**

*Trade responsibly. Past performance does not guarantee future results.*

