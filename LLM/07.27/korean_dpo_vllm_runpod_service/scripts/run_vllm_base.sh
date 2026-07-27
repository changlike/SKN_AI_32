#!/usr/bin/env bash

# 오류 발생 시 즉시 스크립트를 종료합니다.
set -e

# 프로젝트 루트로 이동합니다.
cd "$(dirname "$0")/.."

# .env 파일의 값을 현재 셸 환경변수로 내보냅니다.
set -a
source .env
set +a

# Base 모델을 OpenAI 호환 vLLM 서버로 실행합니다.
exec vllm serve "${BASE_MODEL_NAME}" \
  --host 0.0.0.0 \
  --port "${VLLM_PORT:-8001}" \
  --api-key "${VLLM_API_KEY}" \
  --served-model-name "${VLLM_MODEL_NAME}" \
  --dtype auto \
  --gpu-memory-utilization 0.90 \
  --max-model-len 4096 \
  --generation-config vllm
