@echo off
cd /d %~dp0react_frontend
if not exist node_modules (
  echo [INFO] React package installation...
  call npm install
)
if not exist .env copy /Y .env.example .env >nul 2>&1
call npm run dev
