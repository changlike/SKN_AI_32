#!/usr/bin/env bash

# 스크립트 실행 중 오류가 발생하면 즉시 종료합니다.
set -e

# 현재 스크립트가 저장된 프로젝트 폴더로 이동합니다.
cd "$(dirname "$0")"

# 프로젝트의 메인 파이썬 파일을 실행합니다.
python3 main.py
