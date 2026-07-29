@echo off
REM 현재 배치 파일이 위치한 프로젝트 폴더로 이동합니다.
cd /d %~dp0

REM 프로젝트의 메인 파이썬 파일을 실행합니다.
python main.py

REM 실행 결과를 확인할 수 있도록 콘솔 창을 유지합니다.
pause
