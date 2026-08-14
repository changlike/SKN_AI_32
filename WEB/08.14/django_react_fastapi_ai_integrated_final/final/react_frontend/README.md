# React Frontend

이 프로젝트는 기존 `django_web`의 화면 역할을 React(Vite) 프로젝트로 분리한 프론트엔드입니다.

## 실행

```bash
cd react_frontend
copy .env.example .env
npm install
npm run dev
```

브라우저에서는 `http://127.0.0.1:5173`으로 접속합니다.

## 통신 구조

```text
Browser / React :5173
        ↓
Django JSON API :8000
        ↓
FastAPI AI      :8001
        ↓
ChromaDB / OpenAI / AI Models / MySQL
```

React에는 FastAPI 주소를 설정하지 않습니다. RAG, 이미지 캡셔닝, Stable Diffusion 이미지 생성, STT, TTS 요청과 생성 파일 조회는 모두 Django API를 경유합니다.

## 주요 화면

- `/` 홈 / 최근 게시글
- `/login` 로그인
- `/signup` 회원가입
- `/profile` 회원정보 조회·수정·탈퇴
- `/boards` 게시글 목록·검색·페이징
- `/boards/create` 게시글 등록
- `/boards/:id` 게시글 상세
- `/boards/:id/edit` 본인 글 수정
- `/admin/members` 관리자 회원 활성/비활성 관리
- `/rag` 문서 + 게시글 RAG 검색
- `/ai` 이미지 캡셔닝 / 이미지 생성 / STT / TTS
