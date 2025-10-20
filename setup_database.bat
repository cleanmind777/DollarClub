@echo off
echo Setting up DollarClub Trading Platform Database...

REM Set database connection parameters
set DB_HOST=localhost
set DB_PORT=5432
set DB_NAME=dollarclub
set DB_USER=postgres
set DB_PASSWORD=password

echo.
echo Database Configuration:
echo Host: %DB_HOST%
echo Port: %DB_PORT%
echo Database: %DB_NAME%
echo User: %DB_USER%
echo.

REM Check if psql is available
where psql >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: psql command not found. Please install PostgreSQL client tools.
    echo Download from: https://www.postgresql.org/download/
    pause
    exit /b 1
)

REM Set PGPASSWORD environment variable
set PGPASSWORD=%DB_PASSWORD%

echo Creating database schema...
psql -h %DB_HOST% -p %DB_PORT% -U %DB_USER% -d %DB_NAME% -f init_database.sql

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ✅ Database setup completed successfully!
    echo.
    echo You can now:
    echo 1. Start the backend server
    echo 2. Run database migrations (if needed)
    echo 3. Test the application
) else (
    echo.
    echo ❌ Database setup failed!
    echo Please check your database connection and try again.
)

echo.
pause
