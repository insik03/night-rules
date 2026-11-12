@echo off
setlocal
cd /d "%~dp0"
if not exist "Builds\Windows\NightRulesPrototype.exe" (
    echo Windows game build not found in Builds\Windows.
    pause
    exit /b 1
)
start "" "Builds\Windows\NightRulesPrototype.exe" -NRFinale -windowed -ResX=1600 -ResY=900
