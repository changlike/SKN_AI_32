@echo off
REM Django 프로젝트 디렉터리로 이동합니다.
cd /d "%~dp0django_web"
REM Django 전용 가상환경을 활성화합니다.
call .venv\Scripts\activate.bat
REM 웹 프론트/회원/게시판 서버를 8000 포트에서 실행합니다.
python manage.py runserver 8000
