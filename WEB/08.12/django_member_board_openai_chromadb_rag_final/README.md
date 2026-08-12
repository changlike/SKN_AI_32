# Django Member Board MVT 프로젝트

## 1. 구현 기능

- MySQL 연동 및 Django Migration 기반 테이블 생성
- 사용자 정의 `Member(AbstractUser)` 모델
- 회원가입 / 로그인 / 로그아웃 / 회원정보 조회 / 수정 / 탈퇴
- Django 세션 기반 로그인 상태 유지(30분 비활성 만료)
- 비밀번호 안전한 해시 저장(`set_password`, `UserCreationForm`)
- 관리자 `is_staff`, `is_superuser` 권한 적용
- 관리자의 회원 목록 조회 및 로그인 허용/제한(`is_active`) 처리
- 게시글 목록 / 상세 / 등록 / 수정 / 삭제 CRUD
- 제목/내용 검색과 10개 단위 페이징
- 로그인한 회원만 게시글 등록 가능
- 작성자 본인만 게시글 수정 가능
- 작성자 본인 또는 관리자만 게시글 삭제 가능
- 게시글 첨부파일 업로드
- 게시글 조회수 증가
- Django Admin 제공


## 2. PyCharm에서 프로젝트 열기

1. ZIP 압축을 풉니다.
2. PyCharm → **Open** → `django_member_board_mvt` 폴더를 선택합니다.
3. Python 3.11 가상환경을 생성합니다.
4. PyCharm Terminal에서 다음을 실행합니다.

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

> Windows에서 `mysqlclient` 설치가 실패하면 Python 버전에 맞는 wheel 제공 여부와 MySQL/MariaDB C Connector 환경을 확인하십시오. Python 3.11 환경을 권장합니다.

## 3. MySQL 준비

MySQL Workbench에서 `db/create_database.sql`을 실행합니다. 또는 root 계정으로 아래 파일을 실행합니다.

```sql
SOURCE C:/경로/django_member_board_mvt/db/create_database.sql;
```

`.env.example`을 복사하여 `.env` 파일을 만듭니다.

```powershell
Copy-Item .env.example .env
```

MySQL 계정이 다르면 `.env`의 `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`를 수정합니다.

## 4. Django DB 테이블 생성

사용자 정의 User 모델은 **첫 migrate 전에** `AUTH_USER_MODEL`로 설정되어 있으므로, 프로젝트를 받은 상태 그대로 다음 명령을 실행합니다.

```powershell
python manage.py makemigrations members boards
python manage.py migrate
```

## 5. 관리자 계정과 데모 데이터 생성

수업용 데모 계정과 글을 한 번에 만들 수 있습니다.

```powershell
python manage.py seed_demo
```

데모 계정:

- 관리자: `admin` / `admin1234!`
- 일반회원: `user01` / `pass1234!`
- 일반회원: `user02` / `pass1234!`

직접 superuser를 만들고 싶으면 다음 명령도 사용할 수 있습니다.

```powershell
python manage.py createsuperuser
```

## 6. 서버 실행

```powershell
python manage.py runserver
```

브라우저 접속:

```text
http://127.0.0.1:8000/
```

Django 관리자:

```text
http://127.0.0.1:8000/admin/
```

## 7. 세션과 권한 동작

로그인에 성공하면 `django.contrib.auth.login()`이 Django 세션에 인증 사용자 정보를 저장합니다. 이후 `AuthenticationMiddleware`가 매 요청마다 해당 세션을 읽어 `request.user`를 구성합니다.

- 글 등록: `@login_required`
- 글 수정: `board.author_id == request.user.id`
- 글 삭제: 작성자 본인 **또는** `is_staff/is_superuser`
- 관리자 회원관리: `user_passes_test()`로 관리자 검사
- 로그인 제한 회원: `is_active=False`이면 Django 기본 인증에서 로그인할 수 없음

화면에서 버튼을 숨기는 것만으로 보안을 처리하지 않고, `boards/views.py`에서 서버 측 권한 검사를 다시 수행하므로 URL을 직접 입력해도 타인의 글을 수정/삭제할 수 없습니다.

## 8. ORM 예제

```python
# 전체 게시글 조회: SELECT ... ORDER BY id DESC와 유사합니다.
Board.objects.all()

# 작성자 JOIN 최적화 조회입니다.
Board.objects.select_related("author").all()

# 제목 또는 내용 검색입니다.
Board.objects.filter(Q(title__icontains="Django") | Q(content__icontains="Django"))

# 특정 회원의 게시글을 역참조합니다.
request.user.boards.all()

# 게시글 INSERT입니다.
Board.objects.create(author=request.user, title="제목", content="내용")
```

## 9. 프로젝트 구조

```text
django_member_board_mvt/
├─ config/                 # settings, 최상위 URL, WSGI
├─ members/                # 회원 Model/Form/View/URL/Admin
├─ boards/                 # 게시글 Model/Form/View/URL/Admin
├─ templates/              # Django HTML Template
│  ├─ members/
│  └─ boards/
├─ static/css/             # 프론트 스타일
├─ media/                  # 실행 후 업로드 파일 저장
├─ db/create_database.sql  # MySQL DB/계정 생성
├─ .env.example            # 환경변수 예시
├─ requirements.txt
├─ manage.py
└─ README.md
```

---

# 10. OpenAI LLM + ChromaDB RAG 추가 기능

이 프로젝트에는 기존 회원/게시판 기능을 유지하면서 `rag` 앱이 추가되어 있습니다.

## RAG 근거 데이터

- `docs/` 폴더의 제공 PDF 5개
- MySQL의 Django 게시글(`Board`) 전체

PDF는 PyPDF로 페이지 텍스트를 추출하고 청크 분할한 뒤 OpenAI `text-embedding-3-small` 임베딩으로 변환합니다. 게시글은 제목, 작성자, 작성일, 내용을 하나의 검색 문서로 만들어 동일한 임베딩 모델을 적용합니다. 두 종류의 벡터는 로컬 영구 벡터DB인 ChromaDB `django_docs_and_boards` 컬렉션에 저장됩니다.

검색 화면에서는 다음 범위를 선택할 수 있습니다.

- 전체: PDF 문서 + 게시글
- 근거 문서만
- 게시글만

검색된 Top-K 근거와 질문을 OpenAI Responses API에 전달하고, LLM은 검색 근거에 없는 내용을 추측하지 않도록 시스템 지침을 적용합니다. 화면에는 AI 답변과 함께 실제 검색된 문서명/페이지 또는 게시글 번호, 유사도, 원문 링크가 표시됩니다.

## 추가 패키지 설치

기존과 동일하게 다음 한 번의 명령으로 설치합니다.

```powershell
pip install -r requirements.txt
```

추가된 핵심 패키지는 `openai`, `chromadb`, `pypdf`입니다.

## OpenAI 환경변수

`.env.example`을 `.env`로 복사한 뒤 실제 API Key를 입력합니다.

```env
OPENAI_API_KEY=sk-실제_API_Key
OPENAI_CHAT_MODEL=gpt-5.6-luna
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

`OPENAI_API_KEY`는 소스코드에 직접 작성하지 않습니다.

## 최초 RAG 색인

MySQL migration과 데모 데이터 준비 후 다음 명령을 실행합니다.

```powershell
python manage.py rag_reindex
```

문서만 다시 색인하려면:

```powershell
python manage.py rag_reindex --source documents --force
```

게시글만 다시 색인하려면:

```powershell
python manage.py rag_reindex --source boards --force
```

## 실행

```powershell
python manage.py runserver
```

로그인 후 상단 메뉴의 **AI RAG 검색**을 클릭하거나 아래 주소로 이동합니다.

```text
http://127.0.0.1:8000/rag/
```

벡터 검색 JSON API:

```text
/rag/api/search/?q=반품기간&scope=documents&top_k=5
```

## 게시글 변경 반영

RAG 질문 직전에 증분 동기화를 수행합니다. 게시글의 내용 해시가 기존 ChromaDB 메타데이터와 다를 때만 새 임베딩을 생성하므로 변경되지 않은 게시글에 대한 불필요한 OpenAI API 호출을 줄입니다. 삭제된 게시글의 벡터도 다음 동기화에서 제거됩니다.

## 제공 문서 확인

```text
docs/
├─ 멤버십_등급_및_적립_운영_정책.pdf
├─ 장구_로봇청소기_CleanX_사용_설명서.pdf
├─ 승승_스마트워치_Fit_5_사용_설명서.pdf
├─ 임직원_근무_복리후생_핸드북.pdf
└─ 환불_교환_반품_운영_정책.pdf
```

더 상세한 RAG 처리 흐름과 코드 위치는 `RAG_GUIDE.md`를 참고하십시오.
