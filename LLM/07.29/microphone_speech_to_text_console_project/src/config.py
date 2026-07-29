"""
프로젝트의 녹음 설정, 모델 설정 및 저장 경로를 관리합니다.
"""

# 환경 변수 값을 읽기 위해 os 모듈을 가져옵니다.
import os

# 설정 객체를 간결하게 정의하기 위해 dataclass와 field를 가져옵니다.
from dataclasses import dataclass, field

# 운영체제와 무관한 파일 경로 처리를 위해 Path 클래스를 가져옵니다.
from pathlib import Path


@dataclass
class Config:
    """
    음성 녹음 및 Faster-Whisper 변환에 필요한 설정을 보관합니다.
    """

    # 현재 파일의 상위 상위 폴더를 프로젝트 루트 경로로 설정합니다.
    project_root: Path = field(
        default_factory=lambda: Path(__file__).resolve().parent.parent
    )

    # 녹음 WAV 파일을 저장할 폴더 경로를 나중에 설정합니다.
    recordings_dir: Path = field(init=False)

    # 변환 결과 파일을 저장할 폴더 경로를 나중에 설정합니다.
    results_dir: Path = field(init=False)

    # 마이크 녹음 샘플링 주파수를 16kHz로 설정합니다.
    sample_rate: int = 16_000

    # 음성 인식에 적합한 모노 채널 한 개를 사용합니다.
    channels: int = 1

    # WAV 저장 시 사용할 16비트 PCM의 NumPy 자료형 이름을 설정합니다.
    recording_dtype: str = "int16"

    # 메뉴에서 사용할 기본 고정 녹음 시간을 5초로 설정합니다.
    default_duration_seconds: float = 5.0

    # 한 번의 연속 녹음에서 허용할 최대 시간을 10분으로 제한합니다.
    max_recording_seconds: float = 600.0

    # 환경 변수에 값이 없으면 small 모델을 사용합니다.
    model_size: str = field(
        default_factory=lambda: os.getenv("WHISPER_MODEL_SIZE", "small")
    )

    # 환경 변수에 값이 없으면 CPU를 기본 실행 장치로 사용합니다.
    device: str = field(
        default_factory=lambda: os.getenv("WHISPER_DEVICE", "cpu")
    )

    # CPU에서 메모리 사용량을 줄이기 위해 int8 계산을 기본으로 사용합니다.
    compute_type: str = field(
        default_factory=lambda: os.getenv("WHISPER_COMPUTE_TYPE", "int8")
    )

    # 환경 변수에 값이 없으면 한국어 음성 인식을 기본으로 설정합니다.
    language: str | None = field(
        default_factory=lambda: os.getenv("WHISPER_LANGUAGE", "ko") or None
    )

    # 같은 구간을 여러 후보로 탐색하는 빔 탐색 크기를 설정합니다.
    beam_size: int = 5

    # 음성이 없는 구간을 제거하는 VAD 필터를 사용하도록 설정합니다.
    vad_filter: bool = True

    # 문장 안에서 단어별 시간 정보도 계산하도록 설정합니다.
    word_timestamps: bool = True

    def __post_init__(self) -> None:
        """
        dataclass 초기화 후 파일 저장 경로를 구성하고 폴더를 생성합니다.
        """

        # 프로젝트 루트 아래 recordings 폴더를 녹음 저장 경로로 설정합니다.
        self.recordings_dir = self.project_root / "recordings"

        # 프로젝트 루트 아래 results 폴더를 변환 결과 저장 경로로 설정합니다.
        self.results_dir = self.project_root / "results"

        # recordings 폴더가 없으면 상위 폴더까지 함께 생성합니다.
        self.recordings_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        # results 폴더가 없으면 상위 폴더까지 함께 생성합니다.
        self.results_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        # 샘플링 주파수가 올바른 양수인지 검사합니다.
        if self.sample_rate <= 0:
            # 잘못된 샘플링 주파수 설정에 대한 예외를 발생시킵니다.
            raise ValueError("sample_rate는 0보다 커야 합니다.")

        # 채널 수가 모노 또는 스테레오 범위인지 검사합니다.
        if self.channels not in {1, 2}:
            # 지원하지 않는 채널 수에 대한 예외를 발생시킵니다.
            raise ValueError("channels는 1 또는 2여야 합니다.")
