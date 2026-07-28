#!/usr/bin/env bash
# 오류 발생 시 종료합니다.
set -euo pipefail
# 프로젝트 루트로 이동합니다.
cd "$(dirname "$0")/.."
# FastAPI를 외부 접속 가능한 주소에서 실행합니다.
uvicorn app.main:app --host 0.0.0.0 --port 8000
