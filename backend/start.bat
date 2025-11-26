@echo off
REM Personal Growth OS Backend Startup Script
REM Make sure SSH tunnel is running before starting this

echo ========================================
echo Personal Growth OS Backend Server
echo ========================================
echo.
echo IMPORTANT: Ensure SSH tunnel is running:
echo   ssh -L 5432:127.0.0.1:5432 root@139.224.62.197
echo.
echo Starting backend server...
echo Server will be available at: http://localhost:8000
echo API Documentation: http://localhost:8000/docs
echo.

REM Activate virtual environment
call venv\Scripts\activate

REM Start FastAPI server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

pause
