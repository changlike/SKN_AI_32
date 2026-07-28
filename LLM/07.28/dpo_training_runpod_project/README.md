# PyCharm + RunPod + Hugging Face DPO Training Project

## 1. 프로젝트 목적

이 프로젝트는 `prompt`, `chosen`, `rejected` 형식의 선호도 데이터를 준비하고, 
Hugging Face TRL의 `DPOTrainer`와 PEFT LoRA/QLoRA를 사용하여 DPO 학습을 수행합니다. 

학습 후 선호도 정확도를 평가하고 FastAPI로 추론 서비스를 실행할 수 있습니다.

## 2. 프로젝트 구조

```text
dpo_training_runpod_project/
├── app/main.py                         # FastAPI 추론 서버
├── data/raw/preferences.jsonl          # 원본 선호도 데이터
├── data/processed/                     # 검증 완료 데이터
├── scripts/01_prepare_data.py          # 데이터 검증·정제
├── scripts/02_train_dpo.py             # DPO + QLoRA 학습
├── scripts/03_evaluate.py              # 학습 전후 선호도 정확도 비교
├── scripts/run_runpod.sh               # RunPod 전체 실행 자동화
├── src/config.py                       # 환경 설정
├── src/data_utils.py                   # 데이터 처리 공통 함수
├── tests/test_data_utils.py            # 데이터 검증 테스트
├── .env.example
└── requirements.txt
```

## 3. DPO 데이터 형식

각 JSONL 행은 다음 세 필드를 포함해야 합니다.

```json
{"prompt":"질문","chosen":"선호 답변","rejected":"비선호 답변"}
```

좋은 데이터는 chosen과 rejected가 한두 가지 품질 축에서 명확하게 구분되어야 합니다. 사실성, 안전성, 구체성, 형식 준수 등을 동시에 너무 많이 바꾸면 모델이 어떤 차이를 학습해야 하는지 모호해질 수 있습니다.

## 4. PyCharm 로컬 준비

```powershell
cd C:\LLM_workspace\dpo_training_runpod_project
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
copy .env.example .env
python scripts\01_prepare_data.py
pytest -q
```

로컬 Windows 환경에서는 데이터 검증과 테스트를 우선 실행하고, 실제 4비트 학습은 CUDA Linux 환경인 RunPod에서 수행하는 방식을 권장합니다.

## 5. Hugging Face 토큰 설정

`.env` 파일의 `HF_TOKEN`에 Hugging Face Access Token을 입력합니다. 

공개 모델 다운로드만 수행한다면 토큰 없이도 가능할 수 있지만, 모델 업로드나 제한 모델 사용에는 토큰이 필요합니다.

## 6. RunPod 실행

RunPod Pod의 영구 저장 경로인 `/workspace`에 프로젝트를 둡니다.

```bash
cd /workspace
git clone <저장소_URL> dpo_training_runpod_project
cd dpo_training_runpod_project
cp .env.example .env
nano .env
bash scripts/run_runpod.sh
```

저장소가 없다면 PyCharm의 Deployment/SFTP 또는 `scp`로 프로젝트 폴더를 `/workspace/dpo_training_runpod_project`에 복사할 수 있습니다. `.venv`, `outputs`, 캐시 파일은 업로드하지 않는 것이 좋습니다.

## 7. 단계별 개별 실행

```bash
source .venv/bin/activate
python scripts/01_prepare_data.py
python scripts/02_train_dpo.py --epochs 1 --batch-size 1 --gradient-accumulation 8
python scripts/03_evaluate.py
```

GPU가 없거나 4비트 bitsandbytes를 사용하지 않을 때는 다음 옵션을 사용합니다. 다만 CPU 학습은 매우 느립니다.

```bash
python scripts/02_train_dpo.py --no-4bit
```

## 8. FastAPI 실행

학습 완료 후 다음 명령으로 서버를 실행합니다.

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

요청 예시:

```bash
curl -X POST http://127.0.0.1:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt":"GPU 메모리가 부족할 때 파인 튜닝 방법은?","max_new_tokens":200,"temperature":0.7}'
```

## 9. 주요 하이퍼파라미터

- `beta`: 기준 모델에서 벗어나는 정도를 제어합니다. 값이 작으면 선호 신호를 강하게 반영하고, 값이 크면 기준 정책에 더 가깝게 유지하는 경향이 있습니다.
- `learning_rate`: LoRA DPO에서는 일반적으로 전체 파라미터 학습보다 큰 값을 사용할 수 있지만, 데이터가 작으면 과적합에 주의해야 합니다.
- `max_length`: prompt와 answer를 합친 최대 토큰 길이입니다.
- `max_prompt_length`: prompt 부분의 최대 토큰 길이입니다.
- `gradient_accumulation_steps`: 작은 실제 배치를 여러 번 누적하여 큰 유효 배치처럼 학습합니다.

## 10. 실무 데이터 품질 기준

1. chosen은 실제 배포 정책에 맞아야 합니다.
2. rejected는 단순히 문법이 틀린 답보다, 모델이 실제로 생성할 가능성이 있는 열등한 답이 좋습니다.
3. 개인정보, 저작권, 라이선스, 민감정보를 제거해야 합니다.
4. 중복 prompt와 거의 동일한 답변 쌍을 제거해야 합니다.
5. 학습·검증·테스트 데이터가 같은 원문에서 파생되어 누출되지 않도록 해야 합니다.
6. 자동 생성 데이터는 사람 검수를 거쳐야 합니다.

## 11. 주의 사항

샘플 데이터 6개는 파이프라인 실행 확인용입니다. 실제 품질 개선을 기대하려면 도메인별로 충분한 수의 고품질 선호도 쌍과 별도의 홀드아웃 평가 세트가 필요합니다. 학습 데이터에서 계산한 선호도 정확도만으로 일반화 성능을 판단하면 안 됩니다.
