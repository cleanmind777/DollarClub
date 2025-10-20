@echo off
echo Creating backend/.env file...
echo.

if exist .env (
    echo .env file already exists!
    set /p overwrite="Overwrite? (y/N): "
    if /i not "%overwrite%"=="y" (
        echo Cancelled. .env file not modified.
        exit /b 0
    )
)

(
echo # Application Configuration
echo APP_NAME=DollarClub Trading Platform
echo DEBUG=true
echo SECRET_KEY=change-this-to-random-string-in-production
echo.
echo # Database Configuration
echo DATABASE_URL=postgresql://postgres:your_password_here@localhost/dollarclub
echo.
echo # Redis Configuration
echo REDIS_URL=redis://localhost:6379/0
echo.
echo # Google OAuth Configuration
echo # Get from: https://console.cloud.google.com/
echo GOOGLE_CLIENT_ID=
echo GOOGLE_CLIENT_SECRET=
echo GOOGLE_REDIRECT_URI=http://localhost:8001/auth/google/callback
echo.
echo # IBKR OAuth Configuration
echo IBKR_CLIENT_ID=
echo IBKR_CLIENT_SECRET=
echo IBKR_REDIRECT_URI=http://localhost:8001/auth/ibkr/connect
echo.
echo # Script Execution Configuration
echo MAX_SCRIPT_SIZE=10485760
echo MAX_EXECUTION_TIME=3600
echo MAX_CONCURRENT_SCRIPTS=5
echo.
echo # File Storage Configuration
echo SCRIPTS_DIR=scripts
echo UPLOAD_DIR=uploads
echo.
echo # CORS Configuration
echo CORS_ORIGINS=["http://localhost:3000", "http://localhost:5173"]
) > .env

echo.
echo ✅ .env file created successfully!
echo.
echo ⚠️  IMPORTANT: Edit backend\.env and update:
echo    1. DATABASE_URL - Your PostgreSQL password
echo    2. GOOGLE_CLIENT_ID - From Google Cloud Console
echo    3. GOOGLE_CLIENT_SECRET - From Google Cloud Console
echo.
echo 📖 See SETUP_GOOGLE_OAUTH.md for detailed instructions
echo.
pause

