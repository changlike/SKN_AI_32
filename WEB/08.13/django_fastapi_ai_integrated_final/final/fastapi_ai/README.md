# fastapi_ai

Django와 연동되는 AI 파이프라인 서버입니다. 기본 포트는 `8001`입니다.

제공 기능은 OpenAI + ChromaDB RAG, MySQL 게시글 색인, PDF 근거 문서 색인, BLIP/NLLB 이미지 캡셔닝, Stable Diffusion XL 이미지 생성, PyTorch Whisper STT, TTS입니다. `docs/`에는 제공된 RAG PDF가 포함되어 있습니다.

`.env.example`을 `.env`로 복사하고 `OPENAI_API_KEY`와 Django와 동일한 MySQL 정보를 설정한 뒤 `python run.py`로 실행하십시오. 상세 실행법은 상위 `README.md`를 참고하십시오.
