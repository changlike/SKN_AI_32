"""프로젝트 전체 환경 변수와 경로를 관리합니다."""
import os  # 운영체제 환경 변수를 읽기 위해 사용합니다.
from pathlib import Path  # Windows와 Linux에서 동일한 방식으로 경로를 처리합니다.
from dotenv import load_dotenv  # 프로젝트 루트의 .env 파일을 읽습니다.

BASE_DIR = Path(__file__).resolve().parent.parent  # app 폴더의 상위 폴더를 프로젝트 루트로 계산합니다.
load_dotenv(BASE_DIR / ".env")  # 현재 작업 폴더와 관계없이 프로젝트 루트의 .env를 로딩합니다.

def _path(value: str, default: Path) -> Path:
    """상대 경로를 프로젝트 루트 기준의 절대 경로로 변환합니다."""
    candidate = Path(value).expanduser() if value else default  # 환경 변수 값이 있으면 사용하고 없으면 기본값을 사용합니다.
    return candidate.resolve() if candidate.is_absolute() else (BASE_DIR / candidate).resolve()  # 절대 경로는 그대로, 상대 경로는 루트와 결합합니다.

class Settings:
    """애플리케이션에서 공유하는 설정 값을 정의합니다."""
    APP_NAME = os.getenv("APP_NAME", "한국어 음성 RAG 고객 상담 서비스")  # 화면과 API 문서에 표시할 이름입니다.
    HOST = os.getenv("HOST", "127.0.0.1")  # 개발 서버가 사용할 IP 주소입니다.
    PORT = int(os.getenv("PORT", "8000"))  # 개발 서버가 사용할 포트 번호입니다.
    DOCUMENT_DIR = _path(os.getenv("DOCUMENT_DIR", "data/docs"), BASE_DIR / "data/docs")  # PDF, TXT, MD 근거 문서 폴더입니다.
    UPLOAD_DIR = _path(os.getenv("UPLOAD_DIR", "storage/uploads"), BASE_DIR / "storage/uploads")  # 브라우저 녹음 파일 저장 폴더입니다.
    AUDIO_DIR = _path(os.getenv("AUDIO_DIR", "storage/audio"), BASE_DIR / "storage/audio")  # TTS 결과 저장 폴더입니다.
    STATIC_DIR = BASE_DIR / "app/static"  # HTML, CSS, JavaScript 폴더입니다.
    RAG_MODE = os.getenv("RAG_MODE", "hybrid").lower()  # hybrid, embedding, keyword 중 검색 방식을 선택합니다.
    EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "intfloat/multilingual-e5-small")  # 의미 검색에 사용할 다국어 임베딩 모델입니다.
    RAG_TOP_K = int(os.getenv("RAG_TOP_K", "4"))  # 질문마다 반환할 최대 근거 수입니다.
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "700"))  # 한 문서 조각의 최대 문자 수입니다.
    CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "100"))  # 인접 조각 사이의 중복 문자 수입니다.
    LOCAL_MODEL_PATH = _path(os.getenv("LOCAL_MODEL_PATH", "models/finetuned_model"), BASE_DIR / "models/finetuned_model")  # 선택적으로 사용할 로컬 파인튜닝 모델 경로입니다.
    USE_LOCAL_MODEL = os.getenv("USE_LOCAL_MODEL", "false").lower() == "true"  # 기본 실행에서는 모델 파일을 요구하지 않습니다.
    BASE_MODEL_NAME = os.getenv("BASE_MODEL_NAME", "Qwen/Qwen2.5-1.5B-Instruct")  # LoRA 어댑터의 원본 모델 이름입니다.
    LLM_DEVICE = os.getenv("LLM_DEVICE", "auto").lower()  # 로컬 LLM 실행 장치입니다.
    MAX_NEW_TOKENS = int(os.getenv("MAX_NEW_TOKENS", "384"))  # 로컬 LLM이 생성할 최대 토큰 수입니다.
    WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "small")  # Faster-Whisper 모델 크기입니다.
    WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "auto").lower()  # STT 실행 장치입니다.
    WHISPER_COMPUTE_TYPE = os.getenv("WHISPER_COMPUTE_TYPE", "int8")  # STT 계산 정밀도입니다.
    TTS_PROVIDER = os.getenv("TTS_PROVIDER", "edge")  # edge 또는 pyttsx3 중 우선 공급자입니다.
    EDGE_TTS_VOICE = os.getenv("EDGE_TTS_VOICE", "ko-KR-SunHiNeural")  # Edge TTS 한국어 음성입니다.
    EDGE_TTS_RATE = os.getenv("EDGE_TTS_RATE", "+0%")  # Edge TTS 발화 속도입니다.

settings = Settings()  # 다른 모듈이 가져다 사용할 설정 객체를 한 번 생성합니다.
