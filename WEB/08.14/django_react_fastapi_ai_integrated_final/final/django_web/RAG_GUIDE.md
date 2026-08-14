# Django RAG Gateway 안내

이 통합본에서 Django `rag` 앱은 OpenAI나 ChromaDB를 직접 실행하지 않습니다. 로그인된 사용자의 질문을 검증하고 `FASTAPI_BASE_URL`의 `/api/rag/query`로 전달한 뒤 결과를 Django 템플릿에 표시합니다.

실제 PDF 로딩, MySQL 게시글 읽기, OpenAI Embedding, ChromaDB 검색, LLM 답변 생성은 모두 `../fastapi_ai` 프로젝트에서 수행합니다.

실행 순서는 FastAPI `8001` → Django `8000`입니다. 자세한 설정은 상위 `README.md`를 참고하십시오.
