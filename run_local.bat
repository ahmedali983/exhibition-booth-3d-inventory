@echo off
cd /d "%~dp0"
echo ExpoVault local website: http://127.0.0.1:8000/
echo Press Ctrl+C to stop. Keep this window open while browsing.
start "" "http://127.0.0.1:8000/"
where py >nul 2>&1
if %errorlevel%==0 (py -m http.server 8000 --bind 127.0.0.1) else (python -m http.server 8000 --bind 127.0.0.1)
pause
