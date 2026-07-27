#!/usr/bin/env bash

# 오류가 발생하면 즉시 스크립트를 종료합니다.
set -e

# 프로젝트 루트로 이동합니다.
cd "$(dirname "$0")/.."

# .env 파일의 값을 현재 셸에 내보냅니다.
set -a
source .env
set +a

# FastAPI 서비스를 외부 접속 가능한 주소와 포트로 실행합니다.
exec uvicorn app.main:app \
  --host "${FASTAPI_HOST:-0.0.0.0}" \
  --port "${FASTAPI_PORT:-8000}" \
  --workers 1
