"""프로젝트 전역 설정을 정의하는 모듈입니다."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


# 프로젝트의 최상위 디렉터리를 계산합니다.
# __file__은 현재 config.py 파일 경로이고, parents[1]은 프로젝트 루트입니다.
PROJECT_ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    """환경 변수와 .env 파일에서 설정값을 읽는 클래스입니다."""

    # Hugging Face 인증 토큰입니다. 공개 모델만 사용할 때는 비워 둘 수 있습니다.
    hf_token: str | None = None

    # DPO 학습의 시작점이 되는 사전학습 또는 지시학습 모델 이름입니다.
    base_model: str = "Qwen/Qwen2.5-0.5B-Instruct"

    # 학습 결과로 저장되는 LoRA Adapter 경로입니다.
    adapter_path: Path = PROJECT_ROOT / "outputs" / "dpo_adapter"

    # FastAPI 서버가 바인딩할 네트워크 주소입니다.
    host: str = "0.0.0.0"

    # FastAPI 서버 포트 번호입니다.
    port: int = 8000

    # .env 파일을 자동으로 읽고, 정의되지 않은 추가 환경 변수는 무시합니다.
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


# 다른 모듈에서 동일한 설정 객체를 재사용하도록 한 번만 생성합니다.
settings = Settings()
