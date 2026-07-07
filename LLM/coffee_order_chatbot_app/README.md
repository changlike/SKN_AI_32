# Coffee Order AI Chatbot

FastAPI + OpenAI + PyTorch 기반 커피 주문 챗봇 예제입니다.

## 주요 기능

- PyTorch 간단 의도 분류 모델
- OpenAI ChatGPT 자연어 응답 생성
- 커피 메뉴 추천
- 장바구니 담기
- 데모 결제 진행 안내
- HTML/CSS/JavaScript 기반 웹 UI

## 실행 방법

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload
```

브라우저에서 접속합니다.

```text
http://127.0.0.1:8000
```

## OpenAI API 키 설정

`.env` 파일에 API 키를 입력합니다.

```text
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_MODEL=gpt-4o-mini
```

## 실습 내용

- 간단 회원가입과 로그인 기능 추가
- 회원정보, 메뉴정보, 주문내역 및 결재정보는 db에 저장 처리
- SQLAlchemy ORM 사용 CRUD 스키마 구현, 모델 서비스 구현
