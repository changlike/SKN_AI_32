# 한국어 LLM 서비스: DPO Fine-tuning + vLLM + FastAPI + RunPod

이 프로젝트는 한국어 사용 LLM 서비스를 만들기 위해 다음 전체 흐름을 실습합니다.

```text
한국어 선호 데이터
        ↓
QLoRA 기반 DPO 학습
        ↓
LoRA Adapter 저장
        ↓
Base 모델과 Adapter 병합
        ↓
vLLM OpenAI 호환 추론 서버
        ↓
FastAPI 서비스 API와 웹 UI
        ↓
Base 모델·DPO 모델 자동 평가와 블라인드 사람 평가
```

## 핵심 개념

### SFT와 DPO의 역할

SFT는 질문과 정답 쌍을 이용해 원하는 답변 형식을 먼저 학습합니다.

SFT(Supervised Fine-Tuning)는 사전에 학습된(Pre-trained) LLM을 정답이 있는 데이터(Label)를 사용하여 특정 목적에 맞게 추가 학습시키는 과정입니다.

SFT(Supervised Fine-Tuning)는 사전에 학습된(Pre-trained) LLM을 정답이 있는 데이터(Label)를 사용하여 특정 목적에 맞게 추가 학습시키는 과정입니다.

DPO는 동일한 질문에 대한 `chosen`과 `rejected` 답변을 이용해 모델이 더 선호되는 답변을 선택하도록 정렬합니다. 

DPO는 별도의 Reward Model 없이 선호 쌍을 직접 최적화할 수 있습니다.

DPO(Direct Preference Optimization)는 사람이 더 선호하는 답변을 직접 학습하여 LLM의 응답 품질을 향상시키는 파인튜닝 기법입니다.

실무적으로는 다음 순서가 안정적입니다.

```text
기반 Instruct 모델
→ 도메인 SFT
→ 선호 데이터 DPO
→ 평가
→ 병합 또는 Adapter 서빙
```

이 프로젝트는 이미 instruction-following 능력이 있는 Qwen Instruct 모델을 기준으로 DPO 단계를 직접 실습합니다. 실제 프로젝트에서는 먼저 충분한 SFT를 수행하는 것이 좋습니다.

## 프로젝트 구조

```text
korean_dpo_vllm_runpod_service/
├── app/
│   ├── api/
│   ├── core/
│   ├── models/
│   ├── services/
│   ├── static/
│   ├── templates/
│   └── main.py
├── data/
│   ├── dpo_train.jsonl
│   ├── dpo_eval.jsonl
│   └── evaluation.jsonl
├── training/
│   ├── validate_dpo_data.py
│   ├── train_dpo_qlora.py
│   └── merge_adapter.py
├── evaluation/
│   ├── generate_predictions.py
│   ├── calculate_metrics.py
│   ├── compare_models.py
│   └── create_blind_review.py
├── scripts/
│   ├── run_fastapi.sh
│   ├── run_vllm_base.sh
│   ├── run_vllm_dpo.sh
│   └── check_gpu.py
├── tests/
│   └── test_api.py
├── .env.example
├── requirements-train.txt
├── requirements-vllm.txt
├── requirements-service.txt
└── README.md
```

# 1단계. RunPod Pod 생성

권장 시작 사양:

- 실습 모델: `Qwen/Qwen2.5-1.5B-Instruct`
- GPU: RTX 4090 24GB, A40 48GB, L40S 48GB 등
- Container Disk: 30GB 이상
- Volume Disk: 50GB 이상
- HTTP 포트: `8000,8001`
- SSH TCP 포트: 템플릿 기본 설정 확인
- Template: RunPod PyTorch

`/root`가 아니라 `/workspace` 아래에 프로젝트와 모델을 저장합니다. Pod가 종료되더라도 Volume Disk 또는 Network Volume에 저장된 결과를 유지하도록 구성합니다.

# 2단계. PyCharm과 RunPod 연결

로컬 프로젝트 경로 예시:

```text
C:\LLM_workspace\korean_dpo_vllm_runpod_service
```

원격 프로젝트 경로:

```text
/workspace/korean_dpo_vllm_runpod_service
```

PyCharm Professional:

1. `Settings → Python Interpreter → Add Interpreter → On SSH`
2. RunPod Connect 화면의 SSH Host, Port, Username 입력
3. 개인키 선택
4. Deployment Mapping에서 로컬 프로젝트와 `/workspace/korean_dpo_vllm_runpod_service` 연결
5. `.venv`, `outputs`, `models`, `checkpoints`는 필요에 따라 업로드 제외

기본 프록시 SSH는 SCP/SFTP가 제한될 수 있습니다. 파일 동기화가 필요하면 RunPod의 direct TCP SSH 설정을 사용하거나 Git 저장소를 이용합니다.

# 3단계. RunPod 설치 (RUNPOD 와 PYCHARM SSH 연결 안될때)

```bash
cd /workspace

git clone <본인_저장소_URL> korean_dpo_vllm_runpod_service
cd korean_dpo_vllm_runpod_service

cp .env.example .env
```

학습용 가상환경:

```bash
python -m venv .venv-train
source .venv-train/bin/activate
python -m pip install --upgrade pip
pip install -r requirements-train.txt
```

서비스용 가상환경:

```bash
python -m venv .venv-service
source .venv-service/bin/activate
python -m pip install --upgrade pip
pip install -r requirements-service.txt
```

vLLM용 가상환경:

```bash
python -m venv .venv-vllm
source .venv-vllm/bin/activate
python -m pip install --upgrade pip
pip install -r requirements-vllm.txt
```

vLLM과 학습 라이브러리를 분리하면 PyTorch·CUDA 의존성 충돌을 줄일 수 있습니다.

# 4단계. GPU 확인

```bash
source .venv-train/bin/activate
python scripts/check_gpu.py
```

# 5단계. DPO 데이터 확인

데이터 한 건은 다음 구조를 사용합니다.

```json
{
  "prompt": [
    {"role": "system", "content": "한국어 고객 상담 AI입니다."},
    {"role": "user", "content": "배송이 너무 늦어요."}
  ],
  "chosen": [
    {"role": "assistant", "content": "불편을 드려 죄송합니다..."}
  ],
  "rejected": [
    {"role": "assistant", "content": "기다리세요."}
  ]
}
```

검증:

```bash
python training/validate_dpo_data.py --file data/dpo_train.jsonl
python training/validate_dpo_data.py --file data/dpo_eval.jsonl
```

중요 원칙:

- chosen과 rejected는 같은 질문에 대한 답변이어야 합니다.
- chosen은 정확성, 친절함, 한국어 자연스러움, 안전성 중 무엇이 우수한지 명확해야 합니다.
- rejected를 일부러 지나치게 나쁘게만 만들면 실제 경계 사례를 학습하지 못합니다.
- 학습·검증·테스트 데이터의 질문이 중복되지 않도록 합니다.
- 개인식별정보와 저작권·라이선스 문제를 점검합니다.

# 6단계. QLoRA DPO 학습

```bash
source .venv-train/bin/activate

python training/train_dpo_qlora.py \
  --base-model Qwen/Qwen2.5-1.5B-Instruct \
  --train-file data/dpo_train.jsonl \
  --eval-file data/dpo_eval.jsonl \
  --output-dir models/dpo_adapter \
  --epochs 1 \
  --batch-size 1 \
  --gradient-accumulation-steps 8 \
  --learning-rate 5e-6 \
  --beta 0.1 \
  --max-length 1024
```

주요 하이퍼파라미터:

- `beta`: 기준 모델에서 얼마나 벗어날지를 제어하는 DPO 핵심 값
- `learning_rate`: DPO는 일반 SFT보다 낮은 학습률부터 시작
- `max_length`: prompt와 답변 전체 최대 길이
- `gradient_accumulation_steps`: 작은 GPU에서 유효 배치 크기를 늘림
- `lora_r`: Adapter 표현력과 메모리 사용량 조절

학습 성공 기준:

- train/eval loss가 정상적으로 기록됨
- `rewards/chosen`과 `rewards/rejected` 간 차이가 개선됨
- Adapter 파일이 `models/dpo_adapter`에 저장됨
- 과적합 없이 별도 평가 데이터 성능이 개선됨

# 7단계. Adapter 병합

vLLM은 LoRA Adapter 직접 서빙도 지원하지만 첫 실습에서는 병합 모델이 단순합니다.

```bash
python training/merge_adapter.py \
  --base-model Qwen/Qwen2.5-1.5B-Instruct \
  --adapter-path models/dpo_adapter \
  --output-dir models/merged_model \
  --dtype bfloat16
```

병합은 4비트 모델에서 직접 수행하지 않고 Base 모델을 BF16 또는 FP16으로 다시 불러와 수행합니다.

# 8단계. vLLM 실행

## Base 모델 서버

```bash
source .venv-vllm/bin/activate
chmod +x scripts/*.sh
./scripts/run_vllm_base.sh
```

## DPO 병합 모델 서버

```bash
source .venv-vllm/bin/activate
./scripts/run_vllm_dpo.sh
```

vLLM 서버 포트는 `8001`입니다.

상태 확인:

```bash
curl http://127.0.0.1:8001/v1/models \
  -H "Authorization: Bearer local-vllm-key"
```

직접 추론:

```bash
curl http://127.0.0.1:8001/v1/chat/completions \
  -H "Authorization: Bearer local-vllm-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "korean-dpo-model",
    "messages": [
      {"role": "system", "content": "정확하고 친절한 한국어 상담 AI입니다."},
      {"role": "user", "content": "배송이 늦어서 화가 납니다."}
    ],
    "temperature": 0.2,
    "max_tokens": 256
  }'
```

# 9단계. FastAPI 서비스 실행

새 SSH 터미널에서:

```bash
source .venv-service/bin/activate
./scripts/run_fastapi.sh
```

접속:

- FastAPI UI: RunPod HTTP Proxy의 8000 포트 URL
- Swagger: `<8000_PROXY_URL>/docs`
- FastAPI 상태: `/api/system/health`
- vLLM 상태: `/api/system/vllm-health`

# 10단계. 서비스 API

채팅:

```bash
curl -X POST http://127.0.0.1:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "환불 정책을 친절하게 설명해 주세요.",
    "system_prompt": "정확하고 친절한 한국어 고객 상담 AI입니다.",
    "temperature": 0.2,
    "max_tokens": 256
  }'
```

# 11단계. 파인튜닝 모델 평가

평가는 다음 네 계층으로 수행합니다.

## 11.1 학습 중 평가

- eval loss
- chosen reward
- rejected reward
- reward margin
- reward accuracy

## 11.2 자동 품질 평가

- Exact Match
- ROUGE-1/2/L
- JSON 형식 준수율
- 거부·안전 응답 규칙
- 한국어 답변 여부의 간단한 휴리스틱

## 11.3 서비스 성능 평가

- 평균 latency
- 중앙값 latency
- P95 latency
- 평균 출력 토큰
- tokens/sec

## 11.4 사람 평가

- 정확성
- 관련성
- 한국어 자연스러움
- 친절성
- 안전성
- Base 대 DPO 블라인드 선호율

Base와 DPO 모델은 동시에 실행하지 않고 같은 vLLM 포트에 하나씩 올려 예측 파일을 생성합니다.

Base 예측:

```bash
./scripts/run_vllm_base.sh
```

다른 터미널:

```bash
source .venv-service/bin/activate

python evaluation/generate_predictions.py \
  --output-file outputs/base_predictions.jsonl
```

Base vLLM 종료 후 DPO 실행:

```bash
./scripts/run_vllm_dpo.sh
```

DPO 예측:

```bash
python evaluation/generate_predictions.py \
  --output-file outputs/dpo_predictions.jsonl
```

지표 계산과 비교:

```bash
python evaluation/calculate_metrics.py \
  --prediction-file outputs/base_predictions.jsonl \
  --output-file outputs/base_metrics.json

python evaluation/calculate_metrics.py \
  --prediction-file outputs/dpo_predictions.jsonl \
  --output-file outputs/dpo_metrics.json

python evaluation/compare_models.py
```

블라인드 평가 CSV:

```bash
python evaluation/create_blind_review.py
```

# 12단계. 결과 해석

DPO 모델이 성공했다고 판단하려면 다음 조건을 함께 봅니다.

- 선호 정확도와 reward margin이 개선됨
- 별도 테스트 데이터에서 한국어 답변 품질이 향상됨
- 안전성과 사실성이 나빠지지 않음
- 특정 문장을 암기하지 않고 새로운 표현에도 일반화함
- 응답 지연과 처리량이 서비스 목표를 충족함
- 사람 블라인드 평가에서 DPO 모델 선호율이 높음

ROUGE 점수 하나만으로 DPO 성공을 판정하지 않습니다. DPO는 표현을 바꿀 수 있으므로 의미·사실성·선호도 평가가 중요합니다.

# 13단계. 운영 시 주의사항

- vLLM API 키는 외부에 공개하지 않습니다.
- RunPod HTTP Proxy 앞에 인증 또는 별도 API Gateway를 둡니다.
- 사용자 입력 길이와 출력 토큰을 제한합니다.
- 로그에 개인정보를 그대로 저장하지 않습니다.
- 모델 버전, 데이터 버전, 평가 결과를 함께 보관합니다.
- Base 모델 라이선스와 데이터 라이선스를 확인합니다.
- Spot Pod는 중단될 수 있으므로 체크포인트를 Volume에 저장합니다.
- 실제 운영에서는 요청 큐, rate limit, 모니터링, HTTPS, 장애 복구를 추가합니다.

# 14단계. 테스트

FastAPI 단위 테스트는 실제 vLLM을 호출하지 않고 모의 응답을 사용합니다.

```bash
source .venv-service/bin/activate
pytest -q
```

실제 GPU 통합 테스트는 vLLM을 실행한 후 웹 UI 또는 Swagger에서 수행합니다.
