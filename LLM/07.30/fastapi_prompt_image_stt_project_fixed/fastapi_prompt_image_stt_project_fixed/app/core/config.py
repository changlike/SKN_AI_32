"""
애플리케이션 전체에서 공유하는 환경 설정값을 정의합니다.
"""

# 운영체제 환경변수에서 설정값을 읽기 위해 os 모듈을 가져옵니다.
import os

# 운영체제와 관계없이 파일 경로를 안전하게 처리하기 위해 Path 클래스를 가져옵니다.
from pathlib import Path

# 설정값을 하나의 불변 객체로 관리하기 위해 dataclass를 가져옵니다.
from dataclasses import dataclass

# 프로젝트 루트의 .env 파일을 환경변수로 불러오기 위해 dotenv를 가져옵니다.
from dotenv import load_dotenv


# 현재 파일을 기준으로 프로젝트 최상위 디렉터리를 계산합니다.
_PROJECT_ROOT = Path(__file__).resolve().parents[2]

# 프로젝트 루트에 .env 파일이 있으면 운영체제 환경변수보다 낮은 우선순위로 읽습니다.
load_dotenv(_PROJECT_ROOT / ".env", override=False)


# 프로젝트 설정값을 구조화하기 위해 dataclass 데코레이터를 적용합니다.
@dataclass(frozen=True)
class Settings:
    """FastAPI, SDXL, 번역 모델과 STT 실행에 필요한 설정값을 보관합니다."""

    # 현재 파일 위치를 기준으로 프로젝트 최상위 디렉터리를 계산합니다.
    project_root: Path = _PROJECT_ROOT

    # Jinja2 HTML 템플릿이 저장된 디렉터리를 지정합니다.
    templates_dir: Path = project_root / "app" / "templates"

    # CSS와 JavaScript 정적 파일이 저장된 디렉터리를 지정합니다.
    static_dir: Path = project_root / "app" / "static"

    # 브라우저에서 녹음한 음성 파일을 저장할 디렉터리를 지정합니다.
    audio_dir: Path = project_root / "storage" / "audio"

    # STT 변환 결과 텍스트 파일을 저장할 디렉터리를 지정합니다.
    transcript_dir: Path = project_root / "storage" / "transcripts"

    # 단계별 이미지, 최종 이미지와 메타데이터를 저장할 디렉터리를 지정합니다.
    generation_dir: Path = project_root / "storage" / "generations"

    # 브라우저 제목과 API 문서에 표시할 애플리케이션 이름을 지정합니다.
    app_name: str = "Korean Prompt & Voice Image Studio"

    # 프롬프트 충실도가 높은 기본 SDXL 모델 ID를 지정합니다.
    image_model_id: str = os.getenv(
        "IMAGE_MODEL_ID",
        "stabilityai/stable-diffusion-xl-base-1.0",
    )

    # 한국어 문장을 영어로 번역할 MarianMT 모델 ID를 지정합니다.
    translation_model_id: str = os.getenv(
        "TRANSLATION_MODEL_ID",
        "Helsinki-NLP/opus-mt-ko-en",
    )

    # 한국어 프롬프트 자동 번역 기능의 활성화 여부를 지정합니다.
    enable_prompt_translation: bool = (
        os.getenv("ENABLE_PROMPT_TRANSLATION", "true").lower() == "true"
    )

    # 이미지 모델에 전달하기 전에 프롬프트를 자동 보강할지 지정합니다.
    enable_prompt_enhancement: bool = (
        os.getenv("ENABLE_PROMPT_ENHANCEMENT", "true").lower() == "true"
    )

    # 사람이 요청되지 않았을 때 인물 생성을 억제할지 지정합니다.
    prevent_unrequested_people: bool = (
        os.getenv("PREVENT_UNREQUESTED_PEOPLE", "true").lower() == "true"
    )

    # SDXL에 사용할 기본 노이즈 제거 단계 수를 지정합니다.
    default_inference_steps: int = int(
        os.getenv("IMAGE_INFERENCE_STEPS", "30")
    )

    # 프롬프트 반영 강도를 제어하는 기본 guidance scale을 지정합니다.
    default_guidance_scale: float = float(
        os.getenv("IMAGE_GUIDANCE_SCALE", "7.0")
    )

    # SDXL의 권장 기본 가로 크기를 지정합니다.
    default_width: int = int(os.getenv("IMAGE_WIDTH", "1024"))

    # SDXL의 권장 기본 세로 크기를 지정합니다.
    default_height: int = int(os.getenv("IMAGE_HEIGHT", "1024"))

    # 중간 이미지를 몇 단계마다 저장할지 지정합니다.
    default_save_interval: int = int(
        os.getenv("IMAGE_SAVE_INTERVAL", "5")
    )

    # CUDA 환경에서 VRAM을 절약하기 위해 CPU 오프로딩을 사용할지 지정합니다.
    enable_cpu_offload: bool = (
        os.getenv("ENABLE_CPU_OFFLOAD", "true").lower() == "true"
    )

    # VAE 디코딩 메모리를 줄이기 위해 slicing을 사용할지 지정합니다.
    enable_vae_slicing: bool = (
        os.getenv("ENABLE_VAE_SLICING", "true").lower() == "true"
    )

    # VAE 디코딩 메모리를 줄이기 위해 tiling을 사용할지 지정합니다.
    enable_vae_tiling: bool = (
        os.getenv("ENABLE_VAE_TILING", "true").lower() == "true"
    )

    # Attention 계산 메모리를 줄이기 위해 slicing을 사용할지 지정합니다.
    enable_attention_slicing: bool = (
        os.getenv("ENABLE_ATTENTION_SLICING", "true").lower() == "true"
    )

    # STT에 사용할 faster-whisper 모델 크기를 지정합니다.
    whisper_model_size: str = os.getenv("WHISPER_MODEL_SIZE", "small")

    # STT 실행 장치를 auto, cpu 또는 cuda 중 하나로 지정합니다.
    whisper_device: str = os.getenv("WHISPER_DEVICE", "auto")

    # CPU STT에서 사용할 계산 정밀도를 지정합니다.
    whisper_compute_type_cpu: str = os.getenv(
        "WHISPER_COMPUTE_TYPE_CPU",
        "int8",
    )

    # GPU STT에서 사용할 계산 정밀도를 지정합니다.
    whisper_compute_type_cuda: str = os.getenv(
        "WHISPER_COMPUTE_TYPE_CUDA",
        "float16",
    )

    # Whisper가 우선적으로 인식할 언어를 지정합니다. 한국어 음성 서비스이므로 기본값은 ko입니다.
    whisper_language: str = os.getenv("WHISPER_LANGUAGE", "ko")

    # 너무 짧은 녹음이 전송되는 것을 막기 위한 최소 녹음 시간을 밀리초로 지정합니다.
    minimum_recording_ms: int = int(os.getenv("MINIMUM_RECORDING_MS", "1200"))

    # 저장 파일을 브라우저에 제공할 URL 접두사를 지정합니다.
    storage_url_prefix: str = "/storage"

    def create_directories(self) -> None:
        """프로그램 실행에 필요한 모든 저장 디렉터리를 생성합니다."""

        # 생성 대상 디렉터리를 하나의 튜플로 구성합니다.
        required_directories = (
            self.audio_dir,
            self.transcript_dir,
            self.generation_dir,
        )

        # 각 디렉터리를 순서대로 확인합니다.
        for directory in required_directories:
            # 디렉터리가 없으면 상위 경로까지 포함하여 생성합니다.
            directory.mkdir(parents=True, exist_ok=True)


# 다른 모듈에서 공통으로 사용할 설정 객체를 한 번 생성합니다.
settings = Settings()
