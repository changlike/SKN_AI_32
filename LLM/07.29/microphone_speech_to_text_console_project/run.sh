#!/usr/bin/env bash

# 실행 중 하나의 명령이라도 실패하면 즉시 스크립트를 종료합니다.
set -e

# 현재 스크립트가 저장된 프로젝트 폴더로 이동합니다.
cd "$(dirname "$0")"

# Python 3 인터프리터로 메인 프로그램을 실행합니다.
python3 main.py
