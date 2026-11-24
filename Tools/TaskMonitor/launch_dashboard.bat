@echo off
title Hampi Battleground Task Monitor Launcher

cd /d "C:\UnrealProjects\Battleground\Tools\TaskMonitor"

:: Check if port 7788 is listening
netstat -ano | findstr ":7788" >nul
if %errorlevel% neq 0 (
    echo Starting Task Monitor Daemon on port 7788...
    start "" pythonw "C:\UnrealProjects\Battleground\Tools\TaskMonitor\task_monitor.py"
    ping 127.0.0.1 -n 3 >nul
) else (
    echo Task Monitor Daemon is already active.
)

:: Launch standalone desktop application window via Edge
echo Opening Task Monitor Dashboard...
start "" "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --app=http://127.0.0.1:7788 --window-size=1150,750

exit
