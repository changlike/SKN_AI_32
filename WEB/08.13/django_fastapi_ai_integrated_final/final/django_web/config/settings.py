"""Django 프로젝트의 전역 환경설정 파일입니다."""
# 파일 시스템 경로 계산을 위해 Path 클래스를 가져옵니다.
from pathlib import Path
# 환경변수 값을 읽기 위해 os 모듈을 가져옵니다.
import os
# 프로젝트 루트의 .env 파일을 읽기 위해 python-dotenv 함수를 가져옵니다.
from dotenv import load_dotenv

# settings.py 기준 두 단계 위 디렉터리를 프로젝트 루트로 지정합니다.
BASE_DIR = Path(__file__).resolve().parent.parent
# 프로젝트 루트의 .env 파일이 존재하면 환경변수로 로딩합니다.
load_dotenv(BASE_DIR / ".env")

# 세션, CSRF 토큰, 비밀번호 재설정 등에 사용하는 비밀키를 환경변수에서 읽습니다.
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-only-secret-key-change-me")
# 문자열 환경변수를 비교하여 개발 디버그 모드를 결정합니다.
DEBUG = os.getenv("DJANGO_DEBUG", "True").lower() == "true"
# 쉼표로 구분된 호스트 문자열을 리스트로 변환합니다.
ALLOWED_HOSTS = [host.strip() for host in os.getenv("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost").split(",") if host.strip()]

# Django 기본 앱과 프로젝트에서 만든 앱을 등록합니다.
INSTALLED_APPS = [
    # Django 관리자 사이트 기능을 제공합니다.
    "django.contrib.admin",
    # 로그인, 로그아웃, 사용자/권한 모델 기능을 제공합니다.
    "django.contrib.auth",
    # 모델 ContentType 정보를 관리합니다.
    "django.contrib.contenttypes",
    # 세션 데이터를 DB에 저장하고 로그인 상태를 유지합니다.
    "django.contrib.sessions",
    # 일회성 성공/오류 메시지를 화면에 출력하도록 지원합니다.
    "django.contrib.messages",
    # CSS, JavaScript, 이미지 등의 정적 파일을 관리합니다.
    "django.contrib.staticfiles",
    # 사용자 정의 회원 모델과 회원 기능을 제공하는 앱입니다.
    "members",
    # 게시판 CRUD 기능을 제공하는 앱입니다.
    "boards",
    # OpenAI + ChromaDB 기반 문서/게시글 RAG 검색 앱입니다.
    "rag",
]

# HTTP 요청/응답 과정에 적용할 미들웨어를 순서대로 등록합니다.
MIDDLEWARE = [
    # 보안 관련 기본 헤더와 설정을 적용합니다.
    "django.middleware.security.SecurityMiddleware",
    # 세션 객체 request.session을 사용할 수 있게 합니다.
    "django.contrib.sessions.middleware.SessionMiddleware",
    # URL 처리 전 공통적인 요청 정규화를 수행합니다.
    "django.middleware.common.CommonMiddleware",
    # POST 요청 위조를 방지하기 위해 CSRF 검증을 수행합니다.
    "django.middleware.csrf.CsrfViewMiddleware",
    # 세션의 사용자 ID를 바탕으로 request.user를 구성합니다.
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    # messages.success(), messages.error() 같은 메시지 기능을 제공합니다.
    "django.contrib.messages.middleware.MessageMiddleware",
    # 클릭재킹 공격을 완화하기 위한 X-Frame-Options 헤더를 적용합니다.
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# 프로젝트의 최상위 URL 설정 모듈을 지정합니다.
ROOT_URLCONF = "config.urls"

# Django 템플릿 엔진과 공통 템플릿 경로를 설정합니다.
TEMPLATES = [
    {
        # Django 기본 템플릿 백엔드를 사용합니다.
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # 프로젝트 루트/templates 폴더에서도 템플릿을 찾도록 합니다.
        "DIRS": [BASE_DIR / "templates"],
        # 각 앱 내부의 templates 폴더를 자동 검색합니다.
        "APP_DIRS": True,
        # 템플릿에서 request, user, messages 등을 사용하기 위한 Context Processor를 설정합니다.
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# WSGI 웹 서버가 사용할 애플리케이션 객체 위치를 지정합니다.
WSGI_APPLICATION = "config.wsgi.application"

# MySQL 데이터베이스 연결 정보를 환경변수 기반으로 설정합니다.
DATABASES = {
    "default": {
        # Django가 mysqlclient 드라이버를 이용해 MySQL과 통신하도록 지정합니다.
        "ENGINE": "django.db.backends.mysql",
        # 사용할 MySQL 데이터베이스 이름을 지정합니다.
        "NAME": os.getenv("DB_NAME", "django_member_board"),
        # MySQL 접속 계정을 지정합니다.
        "USER": os.getenv("DB_USER", "django_user"),
        # MySQL 접속 비밀번호를 지정합니다.
        "PASSWORD": os.getenv("DB_PASSWORD", "django1234!"),
        # MySQL 서버 주소를 지정합니다.
        "HOST": os.getenv("DB_HOST", "127.0.0.1"),
        # MySQL 서버 포트를 지정합니다.
        "PORT": os.getenv("DB_PORT", "3306"),
        # 한글과 이모지를 안정적으로 저장하기 위해 utf8mb4 문자셋을 사용합니다.
        "OPTIONS": {"charset": "utf8mb4"},
    }
}

# Django 기본 비밀번호 검증기를 사용하여 지나치게 단순한 비밀번호를 제한합니다.
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# 프로젝트에서 기본 auth.User 대신 members.Member 모델을 사용자 모델로 사용합니다.
AUTH_USER_MODEL = "members.Member"
# @login_required에서 로그인하지 않은 사용자를 이동시킬 URL 이름입니다.
LOGIN_URL = "members:login"
# 로그인 성공 후 next 값이 없을 때 이동할 기본 URL입니다.
LOGIN_REDIRECT_URL = "boards:list"
# 로그아웃 후 이동할 기본 URL입니다.
LOGOUT_REDIRECT_URL = "home"
# 사용자의 비활성 시간이 30분을 넘으면 세션을 만료시킵니다.
SESSION_COOKIE_AGE = 30 * 60
# 요청이 발생할 때마다 세션 만료 시간을 다시 30분으로 연장합니다.
SESSION_SAVE_EVERY_REQUEST = True

# 사이트의 기본 언어를 한국어로 지정합니다.
LANGUAGE_CODE = "ko-kr"
# 서버와 템플릿에서 사용하는 표준 시간대를 서울로 지정합니다.
TIME_ZONE = "Asia/Seoul"
# Django 번역 기능을 활성화합니다.
USE_I18N = True
# timezone-aware datetime을 사용합니다.
USE_TZ = True

# /static/ URL이 정적 파일을 가리키도록 설정합니다.
STATIC_URL = "static/"
# 프로젝트 공통 static 디렉터리를 추가합니다.
STATICFILES_DIRS = [BASE_DIR / "static"]
# 업로드한 프로필 사진과 게시글 첨부파일의 URL 접두사를 지정합니다.
MEDIA_URL = "media/"
# 업로드 파일을 실제 저장할 디렉터리를 지정합니다.
MEDIA_ROOT = BASE_DIR / "media"
# AutoField보다 큰 정수형 기본 PK 타입을 사용합니다.
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# FastAPI AI 파이프라인 서버의 기본 주소입니다. 브라우저가 아니라 Django 서버가 이 주소로 AI 요청을 전달합니다.
FASTAPI_BASE_URL = os.getenv("FASTAPI_BASE_URL", "http://127.0.0.1:8001")
# 일반 health/RAG HTTP 요청의 최대 대기 시간(초)입니다.
FASTAPI_REQUEST_TIMEOUT = int(os.getenv("FASTAPI_REQUEST_TIMEOUT", "120"))
# Stable Diffusion, Whisper처럼 모델 추론 시간이 길 수 있는 요청의 최대 대기 시간(초)입니다.
FASTAPI_AI_TIMEOUT = int(os.getenv("FASTAPI_AI_TIMEOUT", "600"))
