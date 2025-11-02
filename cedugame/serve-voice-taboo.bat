@echo off
setlocal
REM Serve the project root so phone can access via LAN
cd /d "%~dp0"
python -m http.server 8080 --bind 0.0.0.0
endlocal
