# 한국어 음성 RAG 고객 상담 서비스

이 프로젝트는 `data/docs`의 PDF, TXT, MD 문서를 근거로 고객 문의에 답합니다. 

## 포함된 근거 문서

- 환불교환정책.pdf
- 멤버십정책.pdf
- 제품매뉴얼_스마트워치.pdf
- 제품매뉴얼_로봇청소기.pdf
- 직원핸드북.pdf

## 실행

```powershell
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
copy .env.example .env
python run.py
```

브라우저에서 `http://127.0.0.1:8000`에 접속합니다.

## 중요 설정

- `DOCUMENT_DIR=data/docs`: 실제 근거 문서 폴더입니다.
- `RAG_MODE=hybrid`: 임베딩 의미 검색과 키워드 검색을 결합합니다. 
- 임베딩 모델 다운로드 실패 시 키워드 검색으로 자동 전환합니다.
- `USE_LOCAL_MODEL=false`: 기본값입니다. 파인튜닝 모델 파일 없이 근거 추출형 답변으로 정상 실행됩니다.
- 로컬 파인튜닝 모델을 실제로 배치한 경우에만 `USE_LOCAL_MODEL=true`로 변경합니다.

## STT 주의사항

Faster-Whisper는 첫 음성 요청 때 지정한 Whisper 모델을 다운로드할 수 있으므로 인터넷 연결이 필요합니다. 
브라우저 마이크 권한을 허용해야 하며, 음성 디코딩 문제가 발생하면 Windows에 FFmpeg를 설치하고 터미널을 다시 시작합니다.

```powershell
winget install --id Gyan.FFmpeg --exact
```

다음 순서로 다시 시작하십시오.

1. PyCharm 종료
2. 실행 중인 PowerShell 또는 CMD 종료
3. PyCharm 다시 실행
4. 프로젝트 다시 열기
5. 새 터미널 열기
```
그다음 확인합니다.

```powershell
ffmpeg -version
```

## 상태 확인

브라우저 또는 API에서 `/api/health`를 호출하면 문서 수, 청크 수, 실제 검색 모드, STT 상태, 로컬 모델 사용 여부를 확인할 수 있습니다.

## 예시 질문

- 단순 변심으로 반품하면 배송비는 누가 부담하나요?
- 멤버십 등급 기준을 알려 주세요.
- 스마트워치 배터리 사용 시간은 얼마인가요?
- 로봇청소기가 같은 자리에서 반복해서 멈추면 어떻게 해야 하나요?
