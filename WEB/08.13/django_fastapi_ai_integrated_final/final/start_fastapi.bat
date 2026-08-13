@echo off
REM FastAPI 프로젝트 디렉터리로 이동합니다.
cd /d "%~dp0fastapi_ai"
REM FastAPI 전용 가상환경을 활성화합니다.
call .venv\Scripts\activate.bat
REM Django와 포트가 충돌하지 않도록 AI 서버를 8001에서 실행합니다.
uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
