# Django + FastAPI AI 통합 최종 프로젝트

이 프로젝트는 기존 Django `members`, `boards` 기능을 유지하면서 AI 기능을 FastAPI 서비스로 분리한 통합 예제입니다. Django는 회원가입, 로그인 세션, 권한, 게시판 CRUD, HTML 프론트 페이지를 담당하고 FastAPI는 OpenAI RAG, ChromaDB Vector DB, MySQL 게시글 색인, 이미지 캡셔닝, Stable Diffusion 이미지 생성, Whisper STT, TTS를 담당합니다.

## 1. 최종 구조

```text
final/
├─ django_web/                     # Django 프론트 + 일반 백엔드
│  ├─ members/                     # 기존 회원 기능 유지
│  ├─ boards/                      # 기존 게시판 CRUD 유지
│  ├─ rag/                         # FastAPI 호출 Gateway 역할
│  ├─ templates/rag/
│  │  ├─ search.html               # RAG 검색 화면
│  │  └─ multimodal.html           # 멀티모달 AI 화면
│  ├─ static/js/multimodal.js
│  └─ .env.example
│
└─ fastapi_ai/                     # AI 서비스 파이프라인
   ├─ app/
   │  ├─ main.py                   # FastAPI + CORS + 멀티모달 API
   │  ├─ rag_router.py             # RAG REST API
   │  ├─ database.py               # MySQL 연결
   │  ├─ repositories/
   │  │  └─ board_repository.py    # Django 게시글 읽기
   │  └─ services/
   │     ├─ rag_service.py          # OpenAI + ChromaDB RAG
   │     ├─ document_loader.py      # PDF 청크 생성
   │     ├─ caption_service.py      # 이미지 캡셔닝
   │     ├─ diffusion_service.py    # 이미지 생성
   │     └─ speech_service.py       # STT/TTS
   ├─ docs/                         # 제공된 PDF 근거 문서 포함
   ├─ vector_db/chroma/             # 실행 후 Vector DB 저장
   └─ .env.example
```

## 2. 서비스 흐름

```text
브라우저
  │
  ▼
Django :8000
  ├─ members 로그인/세션/권한
  ├─ boards CRUD
  ├─ /rag/ RAG 화면
  └─ /rag/multimodal/ 멀티모달 화면
          │
          │ 서버 간 HTTP 요청
          ▼
FastAPI :8001
  ├─ OpenAI Embedding / LLM
  ├─ ChromaDB Vector DB
  ├─ MySQL의 Django 게시글 읽기
  ├─ BLIP + NLLB 이미지 캡셔닝
  ├─ Stable Diffusion 이미지 생성
  ├─ Whisper STT
  └─ TTS
```

브라우저의 주요 AI 요청은 FastAPI를 직접 호출하지 않고 Django 동일 Origin `/rag/api/...`로 호출합니다. 따라서 Django 로그인 세션과 CSRF 정책을 유지하면서 일반적인 브라우저 CORS 문제를 피할 수 있습니다. FastAPI에도 `CORSMiddleware`가 적용되어 있어 `http://127.0.0.1:8000`과 `http://localhost:8000`의 직접 API 호출을 허용합니다.

## 3. MySQL 생성

MySQL Workbench 또는 MySQL 콘솔에서 `django_web/db/create_database.sql`을 실행하거나 다음 값과 동일한 DB/계정을 준비합니다.

```sql
CREATE DATABASE IF NOT EXISTS django_member_board
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'django_user'@'localhost' IDENTIFIED BY 'django1234!';
GRANT ALL PRIVILEGES ON django_member_board.* TO 'django_user'@'localhost';
FLUSH PRIVILEGES;
```

MySQL 접속 값은 Django와 FastAPI의 `.env`에서 반드시 동일해야 합니다.

## 4. Django 준비

Windows PowerShell 기준입니다.

```powershell
cd django_web
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

`.env`의 DB 정보를 자신의 MySQL 환경과 맞춥니다. 그 다음 기존 프로젝트처럼 migration을 생성하고 적용합니다.

```powershell
python manage.py makemigrations members
python manage.py makemigrations boards
python manage.py migrate
python manage.py createsuperuser
```

샘플 회원이 필요하면 기존 프로젝트에 포함된 명령도 사용할 수 있습니다.

```powershell
python manage.py seed_demo
```

## 5. FastAPI AI 서버 준비

별도의 터미널을 열어 FastAPI 전용 가상환경을 만듭니다. PyTorch/Transformers/Stable Diffusion 때문에 Django 가상환경과 분리하는 것을 권장합니다.

```powershell
cd fastapi_ai
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

`fastapi_ai/.env`에서 반드시 `OPENAI_API_KEY`를 실제 키로 변경하고 MySQL 값을 Django와 동일하게 설정합니다.

GPU가 있는 환경에서는 설치된 CUDA 버전에 맞는 PyTorch가 필요할 수 있습니다. CPU에서도 실행할 수 있지만 Stable Diffusion XL은 매우 느리고 메모리를 많이 사용합니다.

## 6. 서버 실행 순서

먼저 FastAPI를 8001 포트로 실행합니다.

```powershell
cd fastapi_ai
.\.venv\Scripts\Activate.ps1
python run.py
```

`run.py`는 Django와 충돌하지 않도록 8001 포트로 설정되어 있습니다. 다음 명령으로 직접 실행해도 동일합니다.

```powershell
uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

FastAPI 상태 확인 주소:

```text
http://127.0.0.1:8001/api/health
http://127.0.0.1:8001/docs
```

그 다음 Django를 8000 포트로 실행합니다.

```powershell
cd django_web
.\.venv\Scripts\Activate.ps1
python manage.py runserver 8000
```

Django 접속 주소:

```text
http://127.0.0.1:8000/
```

## 7. RAG 사용 방법

1. Django에서 회원가입 또는 로그인합니다.
2. 상단 `AI RAG 검색` 메뉴를 클릭합니다.
3. 검색 범위를 `문서 + 게시글`, `문서`, `게시글` 중 선택합니다.
4. 질문을 입력하고 `RAG 검색 및 답변 생성`을 클릭합니다.
5. Django가 `/api/rag/query`를 FastAPI에 호출합니다.
6. FastAPI는 `fastapi_ai/docs` PDF 변경분과 MySQL 게시글 변경분을 ChromaDB에 증분 색인합니다.
7. OpenAI Embedding으로 질문 벡터를 만든 뒤 ChromaDB에서 유사 근거를 검색합니다.
8. 검색된 근거만 OpenAI LLM에 전달하여 답변을 생성합니다.
9. 결과에는 PDF 페이지 또는 Django 게시글 링크가 근거로 표시됩니다.

첫 질문은 PDF 전체 임베딩이 수행되므로 시간이 더 걸리고 OpenAI embedding 비용이 발생합니다. 이후 변경되지 않은 문서는 `content_hash`를 비교하여 다시 임베딩하지 않습니다.

전체 강제 재색인은 FastAPI Swagger의 다음 API에서 실행할 수 있습니다.

```text
POST /api/rag/reindex?force=true
```

## 8. 멀티모달 AI 사용 방법

로그인 후 상단 `멀티모달 AI` 메뉴 또는 다음 주소를 사용합니다.

```text
http://127.0.0.1:8000/rag/multimodal/
```

기능은 다음과 같습니다.

- 이미지 캡셔닝: Django 업로드 → FastAPI BLIP → NLLB 한국어 변환 → Django 화면 출력
- 이미지 생성: Django 프롬프트 → FastAPI Stable Diffusion XL → 생성 이미지 URL 출력
- STT: 브라우저 마이크 → 16kHz PCM WAV → Django → FastAPI Whisper → 텍스트 → 이미지 프롬프트 자동 입력
- TTS: Django 텍스트 → FastAPI TTS → WAV 생성 → 브라우저 재생

## 9. CORS 해결 방식

이 프로젝트는 두 단계로 해결합니다.

첫째, 실제 Django UI는 FastAPI를 직접 호출하지 않습니다. 브라우저는 항상 `127.0.0.1:8000/rag/api/...`를 호출하고 Django 서버가 `127.0.0.1:8001/api/...`로 전달합니다. 브라우저 관점에서는 Same Origin이므로 CORS 오류가 발생하지 않습니다.

둘째, FastAPI `main.py`에도 다음 설정이 적용되어 직접 API 개발 테스트도 가능합니다.

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)
```

운영 배포에서는 `CORS_ORIGINS`에 실제 Django 도메인만 지정하고 `*` Origin과 credentials 조합은 사용하지 않는 것이 안전합니다.

## 10. 기존 Django 기능 보존 범위

`members`와 `boards`의 모델, 폼, CRUD View, 로그인/로그아웃/권한 로직은 AI 통합을 위해 구조를 변경하지 않았습니다. FastAPI는 해당 기능을 대체하지 않으며 게시글 RAG 색인을 위해 MySQL을 읽기만 합니다.

게시글이 추가/수정/삭제된 뒤 다음 RAG 질문을 수행하면 FastAPI가 MySQL의 현재 상태와 ChromaDB의 `content_hash`를 비교하여 변경된 게시글만 다시 임베딩하고 삭제된 게시글 벡터는 제거합니다.

## 11. 문제 해결

`FastAPI AI 서버 연결 실패`가 나오면 FastAPI가 8001에서 실행 중인지, `django_web/.env`의 `FASTAPI_BASE_URL`이 동일한지 확인합니다.

`OPENAI_API_KEY가 없습니다`가 나오면 `fastapi_ai/.env`의 API 키를 확인합니다.

`MySQL 연결 오류`가 나오면 두 `.env`의 DB 정보가 같은지, MySQL 서비스가 실행 중인지, `django_member_board` DB와 계정 권한이 있는지 확인합니다.

`members_member` 또는 `boards_board` 테이블이 없다는 오류가 나오면 Django에서 `makemigrations`와 `migrate`를 먼저 실행합니다.

Stable Diffusion 실행 중 CUDA 메모리 오류가 나오면 다른 GPU 프로그램을 종료하거나 `.env`의 이미지 크기를 낮추고, GPU 환경에 맞는 PyTorch를 설치합니다.

마이크는 브라우저 보안 정책 때문에 일반적으로 `localhost`/`127.0.0.1` 또는 HTTPS에서 사용해야 하며 최초 실행 시 브라우저 마이크 권한을 허용해야 합니다.
