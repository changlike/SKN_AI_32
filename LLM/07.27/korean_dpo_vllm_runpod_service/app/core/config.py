"""
FastAPI 서비스와 vLLM 연결 환경설정을 관리합니다.
"""

# 설정 객체를 재사용하기 위해 lru_cache를 가져옵니다.
from functools import lru_cache

# 프로젝트 경로를 계산하기 위해 Path를 가져옵니다.
from pathlib import Path

# .env 기반 설정 클래스를 가져옵니다.
from pydantic_settings import BaseSettings, SettingsConfigDict


# 현재 파일을 기준으로 프로젝트 루트 경로를 계산합니다.
PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """
    환경변수와 .env 파일에 정의된 서비스 설정입니다.
    """

    # 웹 화면과 API 문서에 표시할 애플리케이션 이름입니다.
    app_name: str = "한국어 DPO LLM 서비스"

    # vLLM OpenAI 호환 API의 /v1 주소입니다.
    vllm_base_url: str = "http://127.0.0.1:8001/v1"

    # vLLM 실행 명령에서 지정한 API 인증 키입니다.
    vllm_api_key: str = "local-vllm-key"

    # vLLM에 served-model-name으로 등록한 모델 이름입니다.
    vllm_model_name: str = "korean-dpo-model"

    # FastAPI 서버가 수신할 주소입니다.
    fastapi_host: str = "0.0.0.0"

    # FastAPI 서버가 수신할 포트입니다.
    fastapi_port: int = 8000

    # 평가 JSONL 상대 경로입니다.
    evaluation_file: str = "data/evaluation.jsonl"

    # 평가 결과 저장 상대 경로입니다.
    output_dir: str = "outputs"

    # 프로젝트 루트의 .env 파일을 UTF-8로 읽도록 설정합니다.
    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def evaluation_path(self) -> Path:
        """
        평가 파일을 절대 경로로 변환합니다.
        """

        # 설정 문자열을 Path 객체로 변환합니다.
        path = Path(self.evaluation_file)

        # 절대 경로이면 그대로 반환합니다.
        if path.is_absolute():
            return path

        # 상대 경로이면 프로젝트 루트와 결합합니다.
        return PROJECT_ROOT / path

    @property
    def output_path(self) -> Path:
        """
        출력 디렉터리를 절대 경로로 변환합니다.
        """

        # 설정 문자열을 Path 객체로 변환합니다.
        path = Path(self.output_dir)

        # 절대 경로이면 그대로 반환합니다.
        if path.is_absolute():
            return path

        # 상대 경로이면 프로젝트 루트 아래 경로로 반환합니다.
        return PROJECT_ROOT / path


@lru_cache
def get_settings() -> Settings:
    """
    설정 객체를 한 번 생성하고 같은 프로세스에서 재사용합니다.
    """

    # 새로운 Settings 객체를 생성해 반환합니다.
    return Settings()
