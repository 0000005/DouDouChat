@echo off
setlocal enabledelayedexpansion

:: WeAgentChat Memory Debug Tool
set BASE_URL=http://localhost:8000/api

:START
cls
echo ======================================================
echo          WeAgentChat Memory Debug Tool
echo ======================================================
echo.

set /p SID="Step 1: Enter Session ID to debug (or leave empty to list sessions): "

if "%SID%"=="" (
    echo Listing recent sessions...
    curl.exe -s -X GET "%BASE_URL%/chat/sessions?limit=5"
    echo.
    set /p SID="Now enter a Session ID: "
)

:MENU
cls
echo ======================================================
echo    Debugging Session: %SID%
echo ======================================================
echo [1] Trigger Manual Archive (Generate Memory)
echo [2] View Session Status (Check memory_generated)
echo [3] View Session Messages (Review Context)
echo [4] View Friend's Memories (Gists/Events)
echo [5] View Global Profile Memories
echo [6] Switch Session ID
echo [Q] Quit
echo ======================================================
echo.

set /p CHOICE="Choose an option [1-6, Q]: "

if /i "%CHOICE%"=="1" (
    echo.
    echo Triggering archive for session %SID%...
    curl.exe -X POST "%BASE_URL%/chat/sessions/%SID%/archive"
    echo.
    pause
    goto MENU
)

if /i "%CHOICE%"=="2" (
    echo.
    echo Fetching session info...
    :: We can't easily filter JSON in pure BAT without jq, 
    :: but we can list and let the user look for the ID
    curl.exe -s -X GET "%BASE_URL%/chat/sessions"
    echo.
    echo (Look for ID %SID% and its 'memory_generated' field)
    echo.
    pause
    goto MENU
)

if /i "%CHOICE%"=="3" (
    echo.
    echo Fetching messages for session %SID%...
    curl.exe -s -X GET "%BASE_URL%/chat/sessions/%SID%/messages"
    echo.
    pause
    goto MENU
)

if /i "%CHOICE%"=="4" (
    echo.
    set /p FID="Enter Friend ID to view memories (check session info if unsure): "
    echo Fetching memories for friend !FID!...
    curl.exe -s -X GET "%BASE_URL%/profile/events_gists?friend_id=!FID!"
    echo.
    pause
    goto MENU
)

if /i "%CHOICE%"=="5" (
    echo.
    echo Fetching global profile memories...
    curl.exe -s -X GET "%BASE_URL%/profile/profiles"
    echo.
    pause
    goto MENU
)

if /i "%CHOICE%"=="6" (
    goto START
)

if /i "%CHOICE%"=="Q" (
    exit /b
)

goto MENU
