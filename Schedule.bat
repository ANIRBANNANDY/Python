@echo off
setlocal
:: Configuration
set "PROJECT_DIR=C:\ProcessMonitor"
set "PYTHON_EXE=python.exe"
:: CHANGE THIS PER SERVER:
set "MY_HOSTNAME=server1.xyz.com"

cd /d "%PROJECT_DIR%"

:: --- CHECK HUB (Only if this is Server 1) ---
:: We look for a python process that has "hub.py" in the command line
powershell -Command "Get-CimInstance Win32_Process -Filter \"Name = 'python.exe'\" | Where-Object {$_.CommandLine -like '*hub.py*'} | Exit"
if %errorlevel% neq 0 (
    echo [$(get-date)] Starting Hub.py in background...
    start /B "" %PYTHON_EXE% hub.py %MY_HOSTNAME%
)

:: --- CHECK AGENT ---
:: We look for a python process that has "agent.py" in the command line
powershell -Command "Get-CimInstance Win32_Process -Filter \"Name = 'python.exe'\" | Where-Object {$_.CommandLine -like '*agent.py*'} | Exit"
if %errorlevel% neq 0 (
    echo [$(get-date)] Starting Agent.py in background...
    start /B "" %PYTHON_EXE% agent.py
)

exit
