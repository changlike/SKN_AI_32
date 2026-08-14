# React → Django → FastAPI AI 통합 프로젝트

기존 Django + FastAPI 프로젝트의 서비스 기능을 유지하면서 Django 템플릿 프론트엔드를 별도의 React(Vite) 프로젝트로 분리한 최종 구조입니다.

## 1. 프로젝트 구조

```text
final/
├─ react_frontend/       # 사용자 화면 / React + Vite + Bootstrap
├─ django_web/           # 회원, 세션, 권한, 게시판, 파일, JSON API, FastAPI 프록시
├─ fastapi_ai/           # RAG, ChromaDB, 이미지 캡셔닝, 이미지 생성, STT, TTS
├─ start_react.bat
├─ start_django.bat
├─ start_fastapi.bat
└─ start_all.bat
```

기존 Django 템플릿/CBV는 삭제하지 않았습니다. 따라서 기존 서버 렌더링 기능도 보존되며, 새 React 프론트엔드는 `/api/` JSON API를 통해 같은 모델·폼·권한·서비스 로직을 재사용합니다.

## 2. 요청 흐름

```text
React(5173)
   ↓ HTTP + Django Session + CSRF
Django(8000)
   ├─ 회원/로그인/권한
   ├─ 게시판 CRUD / 파일
   └─ RAG·멀티모달 프록시
          ↓ 서버 간 HTTP
      FastAPI(8001)
          ├─ RAG / Vector DB
          ├─ Image Captioning
          ├─ Stable Diffusion
          ├─ STT
          └─ TTS
```

React가 FastAPI API를 직접 호출하지 않으며, 생성 이미지와 TTS WAV 파일도 Django 프록시를 통해 읽습니다.

## 3. 최초 준비

### MySQL
기존 프로젝트에서 사용하던 MySQL DB/계정과 테이블을 그대로 사용합니다. DB 구조 변경이나 추가 migration은 없습니다.

### Django

```bash
cd django_web
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```

`django_web/.env`의 핵심 설정:

```env
FASTAPI_BASE_URL=http://127.0.0.1:8001
REACT_ALLOWED_ORIGINS=http://127.0.0.1:5173,http://localhost:5173
```

### FastAPI

```bash
cd fastapi_ai
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python run.py
```

FastAPI는 기존과 동일하게 `127.0.0.1:8001`에서 실행합니다.

### React

Node.js가 설치되어 있어야 합니다.

```bash
cd react_frontend
copy .env.example .env
npm install
npm run dev
```

`react_frontend/.env`:

```env
VITE_DJANGO_API_URL=http://127.0.0.1:8000
```

FastAPI 주소는 React `.env`에 작성하지 않습니다.

## 4. 실행 순서

가장 안전한 순서는 다음과 같습니다.

1. MySQL 실행
2. FastAPI 실행 (`8001`)
3. Django 실행 (`8000`)
4. React 실행 (`5173`)
5. 브라우저에서 `http://127.0.0.1:5173` 접속

Windows에서는 `start_all.bat`을 실행하면 세 서버를 각각 별도 터미널로 실행합니다.

## 5. 보존된 서비스 기능

회원가입, Django 세션 로그인/로그아웃, 프로필 조회/수정/사진 업로드, 회원탈퇴, 관리자 회원 활성/비활성 제어, 게시판 목록/검색/페이징/상세/조회수/등록/수정/삭제/첨부파일, 작성자 수정 권한, 작성자 또는 관리자 삭제 권한, RAG 검색, 문서 PDF 근거, 게시글 근거, 이미지 캡셔닝, Stable Diffusion 이미지 생성, 마이크 녹음/STT, TTS 및 FastAPI health 확인 기능을 유지합니다.

## 6. CORS / CSRF / 세션

React와 Django는 포트가 다르므로 `django-cors-headers`를 추가했습니다. 허용 origin은 `.env`의 `REACT_ALLOWED_ORIGINS`로 제한합니다. React의 모든 요청에는 `credentials: include`가 적용되며, POST 요청 전 Django CSRF 토큰을 받아 `X-CSRFToken` 헤더로 전송합니다. 따라서 기존 Django SessionAuthentication 및 CSRF 보호를 제거하지 않습니다.

## 7. React용 Django API

- `/api/home/`
- `/api/members/csrf/`
- `/api/members/session/`
- `/api/members/signup/`
- `/api/members/login/`
- `/api/members/logout/`
- `/api/members/profile/`
- `/api/members/withdraw/`
- `/api/members/admin-list/`
- `/api/boards/`
- `/api/boards/create/`
- `/api/boards/<id>/`
- `/api/boards/<id>/update/`
- `/api/boards/<id>/delete/`
- `/api/ai/rag/query/`
- `/api/ai/documents/<filename>/`
- `/api/ai/health/`
- `/api/ai/caption/`
- `/api/ai/generate/`
- `/api/ai/stt/`
- `/api/ai/tts/`
- `/api/ai/media/.../`

기존 Django HTML URL과 기존 FastAPI URL은 그대로 남아 있습니다.
