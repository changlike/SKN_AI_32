# 한국어 프롬프트 정확도 개선 이미지 생성 프로젝트

## 1. 오류 원인

기존 프로젝트는 한국어 문장을 Stable Diffusion v1.5의 CLIP 텍스트 인코더에 그대로 전달했습니다.

Stable Diffusion v1.5는 영어 중심 프롬프트에서 더 안정적으로 동작하므로 다음 요청의 의미가 충분히 전달되지 않았습니다.

```text
호숫가의 통나무집 이미지 생성해 줘
```

그 결과 통나무집 대신 프롬프트와 무관한 인물 이미지가 생성될 수 있었습니다.

## 2. 개선된 처리 흐름

```text
한국어 입력 또는 마이크 STT
    ↓
한국어 포함 여부 자동 감지
    ↓
"이미지 생성해 줘"와 같은 명령 표현 제거
    ↓
MarianMT 한국어 → 영어 번역
    ↓
핵심 피사체와 구도 자동 보강
    ↓
사람이 요청되지 않았다면 인물 관련 Negative prompt 자동 추가
    ↓
SDXL 이미지 생성
    ↓
단계별 이미지와 최종 이미지 저장
```

## 3. 입력 예시와 변환 예시

사용자 입력:

```text
호숫가의 통나무집 이미지 생성해 줘
```

정리된 원문:

```text
호숫가의 통나무집
```

영어 번역 예시:

```text
A log cabin by a lake
```

실제 이미지 모델 입력 예시:

```text
A log cabin by a lake.
The primary subject is exactly: A log cabin by a lake.
Accurately depict only the requested subject and environment.
The primary subject must be clearly visible, recognizable,
and placed near the center of the composition.
...
```

자동 추가 Negative prompt 예시:

```text
unrelated subject, wrong subject, random composition,
person, people, human, man, woman, face, portrait, crowd
```

## 4. 주요 변경 사항

- Stable Diffusion v1.5 기본 모델을 SDXL Base 1.0으로 변경
- 한국어 자동 감지
- MarianMT 한국어 → 영어 번역
- 이미지 생성 명령 표현 자동 제거
- 핵심 피사체 자동 강조
- 무관한 피사체 자동 억제
- 사람이 요청되지 않은 경우 인물 자동 억제
- 영어 번역 결과 프론트 출력
- 실제 이미지 모델 입력 프론트 출력
- 최종 Negative prompt 프론트 출력
- 원문, 번역문과 실제 생성문을 metadata.json에 저장
- 기존 마이크 녹음 및 STT 기능 유지
- 단계별 이미지 저장 기능 유지

## 5. 프로젝트 실행

### Python 3.11 가상환경 생성

```powershell
py -3.11 -m venv .venv
```

### PowerShell 실행 정책 허용

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

### 가상환경 활성화

```powershell
.\.venv\Scripts\Activate.ps1
```

### 패키지 설치

```powershell
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
```

### 서버 실행

```powershell
python run.py
```

브라우저 접속:

```text
http://127.0.0.1:8000
```


## 5-1. 서버 실행 전 가져오기 점검

다음 명령은 모델을 다운로드하지 않고 FastAPI 애플리케이션 모듈이 정상적으로 로딩되는지 확인합니다.

```powershell
python -c "from app.main import app; print(app.title)"
```

정상일 때 다음 애플리케이션 이름이 출력됩니다.

```text
Korean Prompt & Voice Image Studio
```

기존 오류는 `routes.py`가 `run_generation_job` 함수를 가져오도록 작성되어 있었지만,
`image_service.py`에는 `run_image_generation_job`이라는 다른 이름으로 정의되어 발생했습니다.
최종본에서는 실행 함수 이름을 `run_generation_job`으로 통일하고 이전 이름도 호환 별칭으로 유지했습니다.

## 6. 최초 실행

최초 이미지 생성 요청에서는 다음 모델이 자동으로 다운로드됩니다.

```text
stabilityai/stable-diffusion-xl-base-1.0
Helsinki-NLP/opus-mt-ko-en
```

SDXL 모델은 파일 용량과 메모리 사용량이 크므로 최초 로딩 시간이 오래 걸릴 수 있습니다.

## 7. 권장 프롬프트

간단한 명령보다 장면, 배경, 조명과 표현 방식을 함께 지정하면 결과가 좋아집니다.

```text
아침 햇살이 비치는 고요한 호숫가의 아늑한 통나무집,
집 앞에는 작은 나무 부두가 있고 주변에는 소나무 숲이 있는
사실적인 풍경 사진
```

## 8. VRAM 부족 해결

기본 설정은 CPU 오프로딩을 사용합니다.

```text
ENABLE_CPU_OFFLOAD=true
```

그래도 메모리가 부족하면 `.env`에서 경량 모델로 바꿉니다.

```text
IMAGE_MODEL_ID=stable-diffusion-v1-5/stable-diffusion-v1-5
IMAGE_WIDTH=512
IMAGE_HEIGHT=512
IMAGE_INFERENCE_STEPS=25
```

경량 모델에서도 한국어 자동 번역과 인물 억제 기능은 동일하게 적용됩니다.

## 9. 저장 파일

```text
storage/generations/{job_id}/
├── step_005.png
├── step_010.png
├── ...
├── final.png
└── metadata.json
```

`metadata.json`에는 다음 항목이 저장됩니다.

```text
original_prompt
cleaned_prompt
translated_prompt
enhanced_prompt
user_negative_prompt
final_negative_prompt
model_id
inference_steps
guidance_scale
width
height
seed
```

## 10. 주의 사항

생성형 이미지 모델은 확률 모델이므로 모든 요청에서 결과가 완벽하게 일치한다고 보장할 수는 없습니다. 그러나 한국어 원문을 그대로 입력했던 기존 구조보다 번역, 핵심 피사체 강조, 무관한 인물 억제와 SDXL 적용을 통해 프롬프트 일치도를 크게 높이도록 수정했습니다.

## 500 Internal Server Error 수정 사항

첫 화면 라우터에서 존재하지 않는 `settings.default_steps`를 참조하던 문제를 수정했습니다.
현재는 실제 설정 필드인 `settings.default_inference_steps`를 사용합니다.

서버 실행 전에 다음 검증 명령을 실행하면 애플리케이션 import뿐 아니라 `/` 첫 화면과 `/api/health` 응답까지 확인합니다.

```powershell
python verify_project.py
```

정상 출력에는 다음 항목이 포함됩니다.

```text
[성공] GET / 첫 화면 렌더링 완료: 200 OK
[성공] GET /api/health 상태 확인 완료: 200 OK
```


## STT 400 오류 해결 사항

이 버전은 짧은 한국어 발화가 Whisper VAD에서 제거되는 문제를 해결했습니다.

- 브라우저는 250ms 단위로 녹음 조각을 수집합니다.
- 1.2초보다 짧은 녹음은 서버로 전송하지 않습니다.
- Whisper 1차 인식은 VAD를 사용합니다.
- 결과가 비어 있으면 VAD를 끄고 자동으로 2차 인식합니다.
- 한국어(`ko`)를 기본 언어로 사용합니다.

마이크 아이콘을 누른 뒤 2~5초 정도 또렷하게 말하고, 다시 아이콘을 눌러 녹음을 종료하십시오.
