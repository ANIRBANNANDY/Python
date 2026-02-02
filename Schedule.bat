@echo off
setlocal
:: Configuration: Set your project path and Python location
set "PROJECT_DIR=C:\ProcessMonitor"
set "PYTHON_EXE=python.exe"

cd /d "%PROJECT_DIR%"

:: --- START AGENT ---
tasklist /FI "WINDOWTITLE eq AgentProcess" | find /i "python.exe" >nul
if %errorlevel% neq 0 (
    echo Starting Agent.py...
    start "AgentProcess" /min %PYTHON_EXE% agent.py
)

:: --- START HUB (Only on Server 1) ---
:: Remove these lines if you are deploying to Servers 2-6
tasklist /FI "WINDOWTITLE eq HubProcess" | find /i "python.exe" >nul
if %errorlevel% neq 0 (
    echo Starting Hub.py...
    start "HubProcess" /min %PYTHON_EXE% hub.py
)

exit
