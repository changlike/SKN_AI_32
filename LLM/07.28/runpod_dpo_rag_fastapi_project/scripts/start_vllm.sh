#!/usr/bin/env bash
# 오류 발생 시 종료합니다.
set -euo pipefail
# 프로젝트 루트로 이동합니다.
cd "$(dirname "$0")/.."
# .env 값을 셸 환경변수로 내보냅니다.
set -a; [ -f .env ] && source .env; set +a
# 병합 모델을 OpenAI 호환 vLLM 서버로 실행합니다.
vllm serve "${MERGED_MODEL:-outputs/dpo_merged}" --host 0.0.0.0 --port 8001 --served-model-name "${VLLM_MODEL_NAME:-dpo-korean-model}" --api-key "${VLLM_API_KEY:-local-token}" --dtype auto --max-model-len 2048
