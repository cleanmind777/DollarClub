@echo off
echo Starting DollarClub Trading Platform in Development Mode...

echo.
echo Starting Redis...
start "Redis" cmd /k "redis-server"

echo.
echo Starting PostgreSQL...
net start postgresql-x64-13

echo.
echo Starting Backend...
cd backend
start "Backend" cmd /k "python -m venv venv && venv\Scripts\activate && pip install -r requirements.txt && uvicorn main:app --reload --host 0.0.0.0 --port 8000"

echo.
echo Starting Celery Worker...
start "Celery" cmd /k "cd backend && venv\Scripts\activate && celery -A app.tasks worker --loglevel=info"

echo.
echo Starting Frontend...
cd ..\frontend
start "Frontend" cmd /k "npm install && npm run dev"

echo.
echo All services starting...
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo API Docs: http://localhost:8000/docs
echo.
pause
