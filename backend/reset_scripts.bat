@echo off
echo ============================================================
echo Resetting DollarClub Scripts
echo ============================================================
echo.

echo Step 1: Activating virtual environment...
call .venv\Scripts\activate.bat

echo.
echo Step 2: Clearing database scripts...
python -c "from app.core.database import SessionLocal; from app.models.script import Script; db = SessionLocal(); count = db.query(Script).count(); db.query(Script).delete(); db.commit(); print(f'Deleted {count} scripts from database'); db.close()"

echo.
echo Step 3: Clearing uploaded files...
del /Q scripts\*.py 2>nul
echo Deleted script files from disk

echo.
echo Step 4: Clearing Celery queue...
python -c "from app.tasks.celery_app import celery_app; try: purged = celery_app.control.purge(); print(f'Purged {purged} tasks from queue'); except: print('Queue already empty')"

echo.
echo ============================================================
echo Reset Complete!
echo ============================================================
echo.
echo Next steps:
echo 1. Make sure Celery worker is running
echo 2. Upload a fresh script via frontend
echo 3. Click Run button
echo 4. Script should execute successfully!
echo.
pause

