"""FastAPI 환경설정입니다."""
# 설정 객체 캐시를 위해 lru_cache를 가져옵니다.
from functools import lru_cache
# 경로 타입을 위해 Path를 가져옵니다.
from pathlib import Path
# .env 기반 설정을 위해 BaseSettings를 가져옵니다.
from pydantic_settings import BaseSettings, SettingsConfigDict

# 애플리케이션 설정 필드를 정의합니다.
class Settings(BaseSettings):
    # .env 파일을 UTF-8로 읽고 알 수 없는 키는 무시합니다.
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')
    # 원본 모델 ID입니다.
    base_model: str = 'Qwen/Qwen2.5-0.5B-Instruct'
    # 병합 모델 경로입니다.
    merged_model: Path = Path('outputs/dpo_merged')
    # RAG 인덱스 경로입니다.
    rag_index: Path = Path('outputs/rag_index')
    # 추론 백엔드입니다.
    llm_backend: str = 'transformers'
    # vLLM API 주소입니다.
    vllm_base_url: str = 'http://127.0.0.1:8001/v1'
    # vLLM API 키입니다.
    vllm_api_key: str = 'local-token'
    # vLLM 서비스 모델명입니다.
    vllm_model_name: str = 'dpo-korean-model'
    # 임베딩 모델입니다.
    embedding_model: str = 'intfloat/multilingual-e5-small'
    # 기본 검색 문서 수입니다.
    rag_top_k: int = 3
    # Hugging Face 토큰입니다.
    hf_token: str | None = None

# 설정 객체를 한 번만 생성합니다.
@lru_cache(maxsize=1)
def get_settings() -> Settings:
    # 환경변수를 읽은 Settings 객체를 반환합니다.
    return Settings()
