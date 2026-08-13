# django_web

통합 프로젝트의 Django 웹 애플리케이션입니다. 기존 `members` 회원/인증 기능과 `boards` 게시판 CRUD 기능을 유지하고, `rag` 앱은 FastAPI AI 서버에 요청을 전달하는 Gateway 역할을 담당합니다.

AI 기능은 `/rag/`와 `/rag/multimodal/`에서 사용합니다. Django에는 OpenAI/ChromaDB/PyTorch가 필요하지 않습니다. 상위 `README.md`의 MySQL, `.env`, migration, 실행 순서를 따라 실행하십시오.
