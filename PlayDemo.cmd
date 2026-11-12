@echo off
setlocal
cd /d "%~dp0"
if not exist "Builds\Windows\NightRulesPrototype.exe" (
    echo Windows demo build not found in Builds\Windows.
    pause
    exit /b 1
)
start "" "Builds\Windows\NightRulesPrototype.exe" -windowed -ResX=1280 -ResY=720
