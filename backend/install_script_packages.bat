@echo off
REM Install common packages for user trading scripts (Windows)

echo ======================================================================
echo Installing common packages for user trading scripts...
echo ======================================================================
echo.

REM Check if virtual environment exists
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
    echo.
)

REM Run the Python installation script
python install_script_packages.py

REM Pause so user can see the results
echo.
pause

