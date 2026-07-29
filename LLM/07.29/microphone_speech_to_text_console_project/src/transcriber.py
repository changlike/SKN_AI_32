"""
Faster-Whisper 모델을 사용하여 음성 파일을 텍스트로 변환합니다.
"""

# 변환 결과 데이터 구조를 간결하게 정의하기 위해 dataclass를 가져옵니다.
from dataclasses import dataclass

# 입력 파일 경로를 검사하기 위해 Path 클래스를 가져옵니다.
from pathlib import Path

# Faster-Whisper의 WhisperModel 클래스를 가져옵니다.
from faster_whisper import WhisperModel

# 프로젝트 설정 타입을 가져옵니다.
from src.config import Config


@dataclass
class SegmentResult:
    """
    음성 구간 하나의 시작 시간, 종료 시간 및 문장을 저장합니다.
    """

    # 음성 구간의 시작 시간을 초 단위로 저장합니다.
    start: float

    # 음성 구간의 종료 시간을 초 단위로 저장합니다.
    end: float

    # 음성 구간에서 인식된 문장을 저장합니다.
    text: str


@dataclass
class TranscriptionResult:
    """
    하나의 음성 파일에서 생성된 전체 변환 결과를 저장합니다.
    """

    # 모든 구간의 문장을 결합한 전체 텍스트를 저장합니다.
    text: str

    # 모델이 인식하거나 지정받은 언어 코드를 저장합니다.
    language: str

    # 언어 감지 확률을 저장합니다.
    language_probability: float

    # 구간별 변환 결과 목록을 저장합니다.
    segments: list[SegmentResult]


class SpeechToTextService:
    """
    Faster-Whisper 모델을 로드하고 음성 인식 요청을 처리합니다.
    """

    def __init__(self, config: Config) -> None:
        """
        프로젝트 설정을 저장하고 Faster-Whisper 모델을 로드합니다.
        """

        # 녹음 및 음성 인식 설정 객체를 인스턴스 변수로 저장합니다.
        self.config = config

        # 모델 다운로드 또는 로드가 시작된다는 안내를 출력합니다.
        print(
            f"\nFaster-Whisper '{config.model_size}' 모델을 불러옵니다."
        )

        # 최초 실행에서는 모델 파일을 인터넷에서 다운로드할 수 있음을 안내합니다.
        print("최초 실행 시 모델 다운로드로 시간이 걸릴 수 있습니다.")

        # 지정한 모델 크기, 실행 장치 및 계산 자료형으로 WhisperModel을 생성합니다.
        self.model = WhisperModel(
            config.model_size,
            device=config.device,
            compute_type=config.compute_type,
        )

        # 모델 로드가 완료되었음을 출력합니다.
        print("음성 인식 모델 로드 완료.")

    def transcribe(
        self,
        audio_path: str | Path,
    ) -> TranscriptionResult:
        """
        오디오 파일을 텍스트로 변환하고 구조화된 결과를 반환합니다.
        """

        # 문자열 또는 Path 입력을 Path 객체로 변환합니다.
        path = Path(audio_path)

        # 지정한 오디오 파일이 실제로 존재하는지 검사합니다.
        if not path.exists():
            # 파일이 존재하지 않으면 경로를 포함한 예외를 발생시킵니다.
            raise FileNotFoundError(f"오디오 파일을 찾을 수 없습니다: {path}")

        # Faster-Whisper 모델에 오디오 파일과 변환 옵션을 전달합니다.
        segments_iterator, info = self.model.transcribe(
            str(path),
            language=self.config.language,
            beam_size=self.config.beam_size,
            vad_filter=self.config.vad_filter,
            word_timestamps=self.config.word_timestamps,
            condition_on_previous_text=True,
        )

        # 반복자에서 반환되는 구간별 결과를 저장할 리스트를 생성합니다.
        segment_results: list[SegmentResult] = []

        # 전체 문장을 조합하기 위해 각 구간의 텍스트를 저장할 리스트를 생성합니다.
        text_parts: list[str] = []

        # 모델이 생성한 모든 음성 구간을 순서대로 반복합니다.
        for segment in segments_iterator:
            # 구간의 앞뒤 불필요한 공백을 제거합니다.
            cleaned_text = segment.text.strip()

            # 비어 있지 않은 문장만 최종 결과에 포함합니다.
            if cleaned_text:
                # 현재 구간의 시간과 문장을 SegmentResult 객체로 생성합니다.
                segment_result = SegmentResult(
                    start=float(segment.start),
                    end=float(segment.end),
                    text=cleaned_text,
                )

                # 생성한 구간 결과를 전체 구간 목록에 추가합니다.
                segment_results.append(segment_result)

                # 현재 문장을 전체 텍스트 조합 목록에 추가합니다.
                text_parts.append(cleaned_text)

        # 각 구간의 문장을 공백으로 연결하여 전체 텍스트를 만듭니다.
        full_text = " ".join(text_parts)

        # 모델이 제공한 언어 감지 확률이 없을 경우 0으로 처리합니다.
        language_probability = float(
            getattr(info, "language_probability", 0.0)
        )

        # 전체 텍스트, 언어 정보 및 구간 목록을 하나의 결과 객체로 반환합니다.
        return TranscriptionResult(
            text=full_text,
            language=str(info.language),
            language_probability=language_probability,
            segments=segment_results,
        )
