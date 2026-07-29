#!/usr/bin/env bash

# 명령 실행 중 오류가 발생하면 즉시 종료합니다.
set -e

# 현재 스크립트가 위치한 프로젝트 폴더로 이동합니다.
cd "$(dirname "$0")"

# Python 3로 메인 프로그램을 실행합니다.
python3 main.py
