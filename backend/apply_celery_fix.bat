@echo off
echo ============================================================
echo Applying Celery Task Cleanup Fix
echo ============================================================
echo.

echo Step 1: Activating virtual environment...
call .venv\Scripts\activate.bat

echo.
echo Step 2: Running database migration...
alembic upgrade head

echo.
echo ============================================================
echo Migration Complete!
echo ============================================================
echo.
echo Next steps:
echo 1. Restart Celery worker (Ctrl+C, then restart)
echo 2. Restart backend (Ctrl+C, then restart)
echo 3. Test: Execute script, cancel it, execute another script
echo.
echo Commands to restart:
echo.
echo Celery:
echo   celery -A app.tasks.celery_app worker --loglevel=info --pool=solo
echo.
echo Backend:
echo   uvicorn main:app --reload --port 8001
echo.
pause

