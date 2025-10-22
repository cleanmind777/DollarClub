@echo off
echo ============================================================
echo RESTART SERVICES FOR CANCELLATION FIX
echo ============================================================
echo.
echo This will restart backend and Celery with the cancellation fix.
echo.
echo BEFORE STARTING:
echo 1. Stop your current backend (Ctrl+C)
echo 2. Stop your current Celery worker (Ctrl+C)
echo.
echo THEN run these commands in separate terminals:
echo.
echo ============================================================
echo TERMINAL 1 - BACKEND:
echo ============================================================
echo cd backend
echo .\.venv\Scripts\activate
echo uvicorn main:app --reload --port 8001
echo.
echo ============================================================
echo TERMINAL 2 - CELERY:
echo ============================================================
echo cd backend
echo .\.venv\Scripts\activate
echo celery -A app.tasks.celery_app worker --loglevel=info --pool=solo
echo.
echo ============================================================
echo.
echo WHAT'S FIXED:
echo - Non-blocking readline() with 100ms timeout
echo - Aggressive task termination (SIGTERM then SIGKILL)
echo - Immediate process cleanup
echo - Proper cancellation signal handling
echo.
echo AFTER RESTART:
echo 1. Upload a long-running script
echo 2. Execute it
echo 3. Cancel it after 5-10 seconds
echo 4. Execute another script
echo 5. Should work immediately!
echo.
pause
