@echo off
setlocal enabledelayedexpansion

set PROJECT_ROOT=%~dp0..
set BACKEND_EXE_NAME=wechatagent
set BACKEND_DIST=%PROJECT_ROOT%\build\backend
set BACKEND_WORK=%PROJECT_ROOT%\build\pyinstaller_work
set FRONT_DIR=%PROJECT_ROOT%\front
set VENV_DIR=%PROJECT_ROOT%\server\venv
set VENV_PYTHON=%VENV_DIR%\Scripts\python.exe
set VENV_PYINSTALLER=%VENV_DIR%\Scripts\pyinstaller.exe

echo [1/6] Checking pnpm...
where pnpm >nul 2>nul
if errorlevel 1 (
  echo pnpm not found. Please install pnpm and re-run this script.
  exit /b 1
)

echo [2/6] Checking virtual environment...
if not exist "%VENV_PYTHON%" (
  echo Virtual environment not found at %VENV_DIR%.
  echo Please create it first: python -m venv server\venv
  exit /b 1
)

echo [3/6] Checking PyInstaller in venv...
if not exist "%VENV_PYINSTALLER%" (
  echo PyInstaller not found in venv. Installing...
  "%VENV_PYTHON%" -m pip install pyinstaller
  if errorlevel 1 (
    echo Failed to install PyInstaller.
    exit /b 1
  )
)

echo [4/6] Building backend...
if exist "%BACKEND_DIST%" rmdir /s /q "%BACKEND_DIST%"
if exist "%BACKEND_WORK%" rmdir /s /q "%BACKEND_WORK%"

if exist "%PROJECT_ROOT%\server.spec" (
  "%VENV_PYINSTALLER%" "%PROJECT_ROOT%\server.spec" --distpath "%BACKEND_DIST%" --workpath "%BACKEND_WORK%"
) else if exist "%PROJECT_ROOT%\server\server.spec" (
  "%VENV_PYINSTALLER%" "%PROJECT_ROOT%\server\server.spec" --distpath "%BACKEND_DIST%" --workpath "%BACKEND_WORK%"
) else (
  "%VENV_PYINSTALLER%" "%PROJECT_ROOT%\server\app\cli.py" ^
    --name "%BACKEND_EXE_NAME%" ^
    --collect-data tiktoken ^
    --collect-data tiktoken_ext ^
    --noconfirm ^
    --clean ^
    --onedir ^
    --distpath "%BACKEND_DIST%" ^
    --workpath "%BACKEND_WORK%"
)
if errorlevel 1 (
  echo Backend build failed.
  exit /b 1
)

echo [5/6] Building frontend...
pushd "%FRONT_DIR%"
if not exist "node_modules" (
  call pnpm install
  if errorlevel 1 (
    echo pnpm install failed.
    popd
    exit /b 1
  )
)
call pnpm run build
if errorlevel 1 (
  echo Frontend build failed.
  popd
  exit /b 1
)
popd

echo [6/6] Packaging Electron app...
pushd "%PROJECT_ROOT%"
if not exist "node_modules" (
  call pnpm install
  if errorlevel 1 (
    echo pnpm install failed at root.
    popd
    exit /b 1
  )
)
call pnpm run electron:build
if errorlevel 1 (
  echo Electron packaging failed.
  popd
  exit /b 1
)
popd

echo Done. Output in dist-electron\
exit /b 0
