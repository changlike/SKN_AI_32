#!/usr/bin/env bash
# 오류 발생 시 즉시 종료합니다.
set -euo pipefail
# 프로젝트 루트로 이동합니다.
cd "$(dirname "$0")"
# Python 버전을 확인합니다.
python --version
# GPU 상태를 확인합니다.
nvidia-smi || true
# 가상환경이 없으면 생성합니다.
[ -d .venv ] || python -m venv .venv
# 가상환경을 활성화합니다.
source .venv/bin/activate
# 설치 도구를 갱신합니다.
python -m pip install --upgrade pip setuptools wheel
# 공통 의존성을 설치합니다.
python -m pip install -r requirements.txt
# GPU 서빙용 vLLM을 별도로 설치합니다.
python -m pip install "vllm>=0.8,<1.0" || echo "vLLM 설치 실패: transformers 백엔드로 먼저 실행하십시오."
# .env가 없으면 예제를 복사합니다.
[ -f .env ] || cp .env.example .env
# 다음 명령을 안내합니다.
echo "설치 완료: source .venv/bin/activate"
