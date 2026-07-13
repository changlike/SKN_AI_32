[프로젝트 개요]
FastAPI + LangChain 을 사용해서 pdf 파일 업로드해서 내용 읽어서 요약하는 서비스 

[개발 환경]
windows + vscode | pycharm + python 3.11

[프로젝트 구조]
testLangChain (pdf_summarizer)
 - .venv
 - .env
 - requirements.txt
 - app/
    - main.py
    - core/
        - config.py
    - routers/
        - summarize_router.py
    - services/
        - pdf_service.py
        - summarize_service.py

[패키지 설치 관련]
FastAPI 파일 업로드는 python-multipart 필요함
OpenAI 연동은 langchain-openai 패키지 분리 설치함
PDF 로딩은 langchain-community + pypdf 조합함

pip install -U -r requirements.txt

requirements 파일로 패키지 설치시 충돌이 나면 
pip install -U 패키지명
특히, 랭체인의 경우 최신 버전으로 업데이트 설치해 봄
1. pip 최신화
python -m pip install --upgrade pip
2. 패키지 업그레이드
pip install -U langchain
or 
pip install --upgrade langchain langchain-community langchain-openai

또는 requirements.txt 를 “업그레이드 모드”로 재설치:
pip install --upgrade --requirement requirements.txt

실무에서 가장 안정적인 표준 복구 순서
-------------------------------------
# 1. 가상환경 활성화
.\.venv\Scripts\Activate.ps1

# 2. pip 업그레이드
python -m pip install --upgrade pip

# 3. 핵심 패키지 묶음 업그레이드
pip install -U langchain langchain-community langchain-openai

# 4. 나머지 requirements 설치
pip install -r requirements.txt

# 5. 충돌 검사
pip check
-------------------------------------------

[환경변수 파일 : .env]
OPENAI_API_KEY=프로젝트시크릿키

[프로젝트 실행]
기본 설정으로 실행:
uvicorn app.main:app --reload
ip주소, 포트번호 지정 실행:
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

브라우저에서 확인:
http://127.0.0.1:8000/api/ 
=> 첫페이지의 폼에서 파일 선택 : pdf 파일 업로드
=> 요약 결과 (json) 출력 확인 (response)
