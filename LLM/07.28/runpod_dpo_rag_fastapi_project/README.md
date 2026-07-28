# RunPod DPO Fine-tuning + 평가 + RAG FastAPI

## STEP 03: 강화학습과 피드백 루프

- **RLHF**: 사람이 선호도를 표시한 데이터를 이용해 모델을 사람의 기대에 맞추는 정렬 방법입니다. 전형적으로 SFT 모델, 보상 모델, PPO 학습 단계가 필요합니다.
- **DPO**: 같은 질문에 대한 `chosen`과 `rejected` 답변을 사용해, 별도 보상 모델과 PPO 없이 선호 답변의 상대 로그확률을 직접 높입니다.
- **피드백 루프**: 서비스 로그 수집 → 개인정보 제거 → 좋은/나쁜 답변 쌍 검수 → 재학습 → 독립 평가 → 배포 승인 → 다시 로그 수집의 순환입니다.

본 프로젝트는 `Qwen2.5-0.5B-Instruct + LoRA SFT + LoRA DPO + 평가 + FAISS RAG + FastAPI` 전체 흐름을 제공합니다.

## 실행 순서

```bash
cd /workspace/runpod_dpo_rag_fastapi_project
cp .env.example .env
bash run_runpod.sh
source .venv/bin/activate
python training/01_train_sft.py
python training/02_train_dpo.py
python training/03_merge.py
python training/04_evaluate.py
python rag/build_index.py
bash scripts/start_api.sh
```

브라우저: `http://RUNPOD_IP:8000`

## 평가 지표

- Preference Accuracy: chosen 로그확률이 rejected보다 높은 비율
- ROUGE-L: 기준 답변과 생성 답변의 문자열 구조 유사도
- 평균 생성 지연 시간

작은 예제 데이터는 파이프라인 검증용입니다. 실제 성능 향상에는 별도 검증·평가 세트와 충분한 고품질 선호 데이터가 필요합니다.
