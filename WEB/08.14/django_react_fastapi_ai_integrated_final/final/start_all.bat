@echo off
cd /d %~dp0
start "FastAPI AI - 8001" cmd /k "%~dp0start_fastapi.bat"
timeout /t 2 /nobreak >nul
start "Django API - 8000" cmd /k "%~dp0start_django.bat"
timeout /t 2 /nobreak >nul
start "React Frontend - 5173" cmd /k "%~dp0start_react.bat"
echo.
echo React  : http://127.0.0.1:5173
echo Django : http://127.0.0.1:8000
echo FastAPI: http://127.0.0.1:8001
echo.
echo Browser should open React address only.
