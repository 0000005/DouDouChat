@echo off
setlocal

echo [INFO] Checking for existing processes on ports 8000 (Backend) and 5173 (Frontend)...

:: Kill Backend on port 8000
echo Killing existing Backend process on port 8000...
powershell -Command "Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }"

:: Kill Frontend on port 5173
echo Killing existing Frontend process on port 5173...
powershell -Command "Get-NetTCPConnection -LocalPort 5173 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }"

echo.
echo [INFO] Starting WeAgentChat...

:: Start Backend
echo Starting Backend...
start "WeAgentChat Backend" cmd /k "cd ..\server && venv\Scripts\python -m uvicorn app.main:app --reload --port 8000"

:: Start Frontend
echo Starting Frontend...
start "WeAgentChat Frontend" cmd /k "cd ..\front && pnpm dev"

echo.
echo ==========================================================
echo   WeAgentChat is starting!
echo ==========================================================
echo   Backend API Docs:  http://localhost:8000/docs
echo   Frontend UI:       http://localhost:5173
echo ==========================================================
echo.
echo   Check the new terminal windows for logs.
echo.
pause
