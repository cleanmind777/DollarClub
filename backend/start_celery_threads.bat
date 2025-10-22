@echo off
echo ============================================================
echo Starting Celery Worker with Thread Pool
echo ============================================================
echo.
echo This uses --pool=threads instead of --pool=solo
echo Benefits:
echo - More robust to cancellations
echo - Worker doesn't get stuck
echo - Can handle SIGKILL better
echo - More stable for development
echo.
echo ============================================================

cd backend
call .venv\Scripts\activate.bat

echo Starting Celery worker with thread pool...
celery -A app.tasks.celery_app worker --loglevel=info --pool=threads --concurrency=1

pause

