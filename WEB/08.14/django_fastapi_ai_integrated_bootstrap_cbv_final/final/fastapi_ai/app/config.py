"""FastAPI AI 서비스의 환경 변수와 저장 경로를 한 곳에서 관리합니다."""
# 운영체제에 독립적인 파일 경로 처리를 위해 Path 클래스를 가져옵니다.
from pathlib import Path
# .env 값을 타입 안전하게 읽기 위해 BaseSettings를 가져옵니다.
from pydantic_settings import BaseSettings, SettingsConfigDict

# 현재 파일 기준으로 FastAPI 프로젝트 루트 경로를 계산합니다.
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """RAG, MySQL, 멀티모달 모델, CORS에 필요한 환경설정입니다."""
    # Swagger 문서와 서버 정보에 표시할 애플리케이션 이름입니다.
    app_name: str = "Django Connected FastAPI AI Service"
    # 개발 단계에서 상세 오류 확인 여부를 지정합니다.
    debug: bool = True
    # Django 브라우저 출처를 쉼표로 구분해 지정하며 CORS 허용 목록으로 사용합니다.
    cors_origins: str = "http://127.0.0.1:8000,http://localhost:8000"
    # OpenAI API 인증키이며 실제 값은 .env 파일에 저장합니다.
    openai_api_key: str = ""
    # RAG 답변 생성에 사용할 OpenAI 채팅 모델입니다.
    openai_chat_model: str = "gpt-4o-mini"
    # 문서와 게시글을 벡터로 변환할 OpenAI 임베딩 모델입니다.
    openai_embedding_model: str = "text-embedding-3-small"
    # MySQL 서버 주소입니다.
    db_host: str = "127.0.0.1"
    # MySQL 서버 포트입니다.
    db_port: int = 3306
    # Django와 FastAPI가 함께 사용할 데이터베이스 이름입니다.
    db_name: str = "django_member_board"
    # MySQL 접속 사용자 계정입니다.
    db_user: str = "django_user"
    # MySQL 접속 비밀번호입니다.
    db_password: str = "django1234!"
    # SQL 로그 출력 여부입니다.
    db_echo: bool = False
    # 이미지 캡셔닝에 사용할 BLIP 모델입니다.
    caption_model_id: str = "Salesforce/blip-image-captioning-base"
    # 영어 이미지 캡션을 한국어로 번역할 NLLB 모델입니다.
    translation_model_id: str = "facebook/nllb-200-distilled-600M"
    # 텍스트 프롬프트 기반 이미지 생성에 사용할 Stable Diffusion 모델입니다.
    diffusion_model_id: str = "stabilityai/stable-diffusion-xl-base-1.0"
    # 한국어 음성 인식에 사용할 Whisper 모델입니다.
    whisper_model_id: str = "openai/whisper-small"
    # 업로드 가능한 한 파일의 최대 크기(MB)입니다.
    max_upload_size_mb: int = 15
    # 이미지 생성 기본 반복 횟수입니다.
    default_inference_steps: int = 40
    # 이미지 생성 시 프롬프트 반영 강도의 기본값입니다.
    default_guidance_scale: float = 8.0
    # Stable Diffusion 생성 이미지의 기본 한 변 크기입니다.
    diffusion_image_size: int = 1024
    # 텍스트 청크의 최대 문자 수입니다.
    rag_chunk_size: int = 1000
    # 청크 사이에 겹쳐 유지할 문자 수입니다.
    rag_chunk_overlap: int = 150
    # .env 파일을 UTF-8로 읽고 정의되지 않은 값은 무시합니다.
    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origin_list(self) -> list[str]:
        """쉼표 문자열을 FastAPI CORSMiddleware가 사용할 리스트로 변환합니다."""
        # 빈 항목을 제거하고 앞뒤 공백을 정리하여 반환합니다.
        return [item.strip() for item in self.cors_origins.split(",") if item.strip()]

    @property
    def mysql_url(self) -> str:
        """SQLAlchemy가 사용할 PyMySQL 연결 문자열을 생성합니다."""
        # utf8mb4 문자셋을 명시하여 한글과 이모지를 안정적으로 처리합니다.
        return f"mysql+pymysql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}?charset=utf8mb4"


# 다른 모듈에서 재사용할 단일 Settings 객체를 생성합니다.
settings = Settings()
# 업로드 원본을 임시 저장할 디렉터리를 지정합니다.
UPLOAD_DIR = BASE_DIR / "storage" / "uploads"
# Stable Diffusion 결과 이미지를 저장할 디렉터리를 지정합니다.
GENERATED_DIR = BASE_DIR / "storage" / "generated"
# TTS 음성 파일을 저장할 디렉터리를 지정합니다.
AUDIO_DIR = BASE_DIR / "storage" / "audio"
# FastAPI 자체 테스트 페이지에서 사용하는 정적 파일 경로입니다.
STATIC_DIR = BASE_DIR / "app" / "static"
# FastAPI 자체 테스트 페이지의 Jinja 템플릿 경로입니다.
TEMPLATE_DIR = BASE_DIR / "app" / "templates"
# RAG 근거 PDF가 저장되는 디렉터리입니다.
DOCS_DIR = BASE_DIR / "docs"
# ChromaDB 영구 벡터 데이터 저장 디렉터리입니다.
VECTOR_DB_DIR = BASE_DIR / "vector_db" / "chroma"
# 서버 시작 전에 필요한 모든 디렉터리를 생성합니다.
for directory in (UPLOAD_DIR, GENERATED_DIR, AUDIO_DIR, DOCS_DIR, VECTOR_DB_DIR):
    # 부모 디렉터리까지 함께 만들고 이미 존재해도 오류를 발생시키지 않습니다.
    directory.mkdir(parents=True, exist_ok=True)
