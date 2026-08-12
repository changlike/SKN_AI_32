# OpenAI LLM + ChromaDB RAG 사용 가이드

## 1. 구현 목적

이 프로젝트의 RAG는 두 종류의 근거를 동시에 사용합니다.

1. `docs/` 폴더의 PDF 근거 문서
2. Django MySQL `boards_board` 테이블의 게시글

질문을 입력하면 OpenAI Embeddings API로 질문을 벡터화하고, ChromaDB에서 의미적으로 가까운 청크를 검색한 뒤, 검색 결과만 OpenAI Responses API에 전달하여 한국어 답변을 생성합니다.

## 2. 전체 처리 흐름

```text
[PDF 문서] ── PyPDF ── 청크 분할 ──┐
                                 ├─ OpenAI Embeddings ── ChromaDB
[Django 게시글] ── ORM ───────────┘
                                             │
[사용자 질문] ── OpenAI Embeddings ──────-────┤
                                             ▼
                                      cosine Top-K 검색
                                             │
                                             ▼
                                  검색 근거 + 사용자 질문
                                             │
                                             ▼
                                  OpenAI Responses API
                                             │
                                             ▼
                                    근거 번호 포함 답변
```

## 3. 제공된 docs 문서

프로젝트의 `docs/` 폴더에는 제공된 ZIP의 PDF 5개가 포함되어 있습니다.

- `멤버십_등급_및_적립_운영_정책.pdf`
- `장구_로봇청소기_CleanX_사용_설명서.pdf`
- `승승_스마트워치_Fit_5_사용_설명서.pdf`
- `임직원_근무_복리후생_핸드북.pdf`
- `환불_교환_반품_운영_정책.pdf`

`rag/document_loader.py`가 PDF 페이지의 텍스트를 추출하고 기본 1,000자, 150자 overlap으로 청크를 만듭니다. 각 청크에는 문서 제목, 파일명, 페이지 번호, 청크 번호, 내용 해시가 메타데이터로 저장됩니다.

## 4. ChromaDB 저장 구조

벡터DB 물리 경로는 다음과 같습니다.

```text
vector_db/chroma/
```

컬렉션 이름은 다음과 같습니다.

```text
django_docs_and_boards
```

문서와 게시글을 한 컬렉션에 저장하되 메타데이터의 `source_type`으로 구분합니다.

```text
source_type=document   # PDF 문서
source_type=board      # Django 게시글
```

따라서 검색 화면에서 `전체`, `근거 문서만`, `게시글만`을 선택할 수 있습니다.

## 5. 최초 실행

### 5-1. 가상환경 및 패키지

```powershell
pip install -r requirements.txt
```

### 5-2. 환경변수

```powershell
Copy-Item .env.example .env
```

`.env`에서 다음 항목을 설정합니다.

```env
OPENAI_API_KEY=실제_API_Key
OPENAI_CHAT_MODEL=gpt-5.6-luna
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

API Key는 Git에 커밋하지 않습니다.

### 5-3. MySQL 및 migration

RAG 앱은 검색 벡터를 ChromaDB에 저장하므로 별도 MySQL RAG 테이블 migration은 필요하지 않습니다.

### 5-4. 최초 벡터 색인

모든 작업이 끝난 뒤 rag_index.py 를 명령어로 추가 작성한 다음 실행
rag/management/commans 패키지 추가
rag/management/commans/rag_reindex.py 파일 생성

```powershell
python manage.py rag_reindex
```

PDF 문서만 색인:

```powershell
python manage.py rag_reindex --source documents
```

게시글만 색인:

```powershell
python manage.py rag_reindex --source boards
```

전체 강제 재색인:

```powershell
python manage.py rag_reindex --force
```

## 6. 서버 실행과 검색

```powershell
python manage.py runserver
```

로그인 후:

```text
http://127.0.0.1:8000/rag/
```

예시 질문:

```text
반품 신청은 언제까지 해야 하나요?
멤버십 등급은 어떤 기준으로 결정되나요?
CleanX 로봇청소기 사용 시 주의사항은 무엇인가요?
스마트워치 Fit 5의 주요 기능을 설명해 주세요.
최근 게시글에서 Django 관련 내용을 찾아 요약해 주세요.
```

## 7. 게시글 자동 동기화

질문을 처리하기 전에 `sync_all(force=False)`가 실행됩니다. 게시글 텍스트 해시와 ChromaDB의 기존 해시를 비교하여 새 글이나 수정된 글만 임베딩하고, MySQL에서 삭제된 게시글의 벡터는 ChromaDB에서도 삭제합니다.

따라서 게시글 등록/수정/삭제 후 별도 명령을 실행하지 않아도 다음 RAG 질문 시 최신 상태로 동기화됩니다. 대량 변경 후 미리 색인하고 싶으면 `python manage.py rag_reindex --source boards`를 실행합니다.

## 8. JSON 검색 API

로그인 세션이 있는 상태에서 다음 API도 사용할 수 있습니다.

```text
GET /rag/api/search/?q=반품기간&scope=documents&top_k=5
```

`scope` 값:

- `all`
- `documents`
- `boards`

이 API는 LLM 답변이 아니라 벡터 검색 결과와 유사도, 메타데이터를 JSON으로 반환합니다.

## 9. 주요 파일

```text
rag/
├─ apps.py
├─ forms.py
├─ document_loader.py       # PDF 읽기/청킹
├─ service.py               # OpenAI + ChromaDB + RAG 핵심
├─ views.py                 # 화면/API/PDF 원문 제공
├─ urls.py
└─ management/commands/
   └─ rag_reindex.py        # 일괄 색인 명령

templates/rag/search.html   # RAG 검색 UI
docs/                       # 제공된 PDF 근거 문서
vector_db/chroma/           # 실행 시 생성되는 영구 ChromaDB
```

## 10. 오류 확인

### `OPENAI_API_KEY가 설정되지 않았습니다`

`.env` 파일이 프로젝트 루트의 `manage.py`와 같은 위치에 있는지, `OPENAI_API_KEY`에 실제 키가 입력되어 있는지 확인합니다.

### ChromaDB 설치 오류

Python 3.11 가상환경을 권장하며 먼저 pip를 업그레이드합니다.

```powershell
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

### PDF가 검색되지 않음

```powershell
python manage.py rag_reindex --source documents --force
```

실행 후 `vector_db/chroma/`에 파일이 생성되는지 확인합니다.
