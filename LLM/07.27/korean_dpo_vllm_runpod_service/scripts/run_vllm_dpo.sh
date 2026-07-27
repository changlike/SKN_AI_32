#!/usr/bin/env bash

# 오류 발생 시 즉시 종료합니다.
set -e

# 프로젝트 루트 디렉터리로 이동합니다.
cd "$(dirname "$0")/.."

# .env 설정을 현재 셸 환경변수로 내보냅니다.
set -a
source .env
set +a

# 병합된 DPO 모델 디렉터리가 존재하는지 검사합니다.
if [ ! -d "${MERGED_MODEL_PATH}" ]; then
  echo "병합 모델 경로가 없습니다: ${MERGED_MODEL_PATH}"
  exit 1
fi

# 병합된 DPO 모델을 OpenAI 호환 vLLM 서버로 실행합니다.
exec vllm serve "${MERGED_MODEL_PATH}" \
  --host 0.0.0.0 \
  --port "${VLLM_PORT:-8001}" \
  --api-key "${VLLM_API_KEY}" \
  --served-model-name "${VLLM_MODEL_NAME}" \
  --dtype auto \
  --gpu-memory-utilization 0.90 \
  --max-model-len 4096 \
  --generation-config vllm
