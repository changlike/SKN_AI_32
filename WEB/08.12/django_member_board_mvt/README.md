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
