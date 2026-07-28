#!/usr/bin/env bash

# 오류가 발생하면 즉시 종료하고, 정의되지 않은 변수를 사용하면 실패하게 설정합니다.
set -euo pipefail

# 프로젝트 루트에서 실행되도록 현재 스크립트의 상위 디렉터리로 이동합니다.
cd "$(dirname "$0")/.."

# 가상환경이 없을 때만 생성합니다.
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi

# 현재 셸에서 프로젝트 전용 가상환경을 활성화합니다.
source .venv/bin/activate

# 패키지 설치 도구를 최신 상태로 올립니다.
python -m pip install --upgrade pip setuptools wheel

# 프로젝트 의존성을 설치합니다.
pip install -r requirements.txt

# 원본 DPO 데이터를 검증하고 정제합니다.
python scripts/01_prepare_data.py

# RunPod GPU에서 QLoRA 기반 DPO 학습을 시작합니다.
python scripts/02_train_dpo.py

# 학습 전후 선호도 정확도를 비교합니다.
python scripts/03_evaluate.py
