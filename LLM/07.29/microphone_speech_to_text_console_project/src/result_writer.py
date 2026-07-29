"""
음성 인식 결과를 사람이 읽는 TXT와 프로그램용 JSON 파일로 저장합니다.
"""

# 결과 데이터를 JSON 형식으로 저장하기 위해 json 모듈을 가져옵니다.
import json

# 저장 파일명에 날짜와 시간을 포함하기 위해 datetime을 가져옵니다.
from datetime import datetime

# 파일 경로를 처리하기 위해 Path 클래스를 가져옵니다.
from pathlib import Path

# 프로젝트 설정 타입을 가져옵니다.
from src.config import Config

# 음성 인식 결과 타입을 가져옵니다.
from src.transcriber import TranscriptionResult


def save_transcription_result(
    config: Config,
    result: TranscriptionResult,
    source_audio_path: str | Path,
) -> dict[str, Path]:
    """
    변환 결과를 TXT와 JSON 파일로 저장하고 두 경로를 반환합니다.
    """

    # 현재 날짜와 시간을 파일명에 사용할 문자열로 변환합니다.
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

    # 텍스트 결과를 저장할 TXT 파일 경로를 생성합니다.
    text_path = config.results_dir / f"transcription_{timestamp}.txt"

    # 구조화된 결과를 저장할 JSON 파일 경로를 생성합니다.
    json_path = config.results_dir / f"transcription_{timestamp}.json"

    # TXT 파일에 기록할 문자열 목록을 생성합니다.
    text_lines = [
        f"원본 오디오: {Path(source_audio_path).resolve()}",
        f"감지 언어: {result.language}",
        f"언어 확률: {result.language_probability:.6f}",
        "",
        "[전체 텍스트]",
        result.text,
        "",
        "[구간별 텍스트]",
    ]

    # 모든 음성 구간을 순서대로 반복합니다.
    for segment in result.segments:
        # 시작 시간, 종료 시간 및 문장을 TXT 문자열 목록에 추가합니다.
        text_lines.append(
            f"[{segment.start:.2f} ~ {segment.end:.2f}] {segment.text}"
        )

    # TXT 파일을 UTF-8 쓰기 모드로 엽니다.
    with text_path.open(
        mode="w",
        encoding="utf-8",
    ) as text_file:
        # 모든 텍스트 줄을 줄바꿈으로 연결하여 파일에 기록합니다.
        text_file.write(
            "\n".join(text_lines)
        )

    # JSON 파일에 저장할 사전 데이터를 구성합니다.
    json_data = {
        "source_audio": str(Path(source_audio_path).resolve()),
        "language": result.language,
        "language_probability": result.language_probability,
        "text": result.text,
        "segments": [
            {
                "start": segment.start,
                "end": segment.end,
                "text": segment.text,
            }
            for segment in result.segments
        ],
    }

    # JSON 파일을 UTF-8 쓰기 모드로 엽니다.
    with json_path.open(
        mode="w",
        encoding="utf-8",
    ) as json_file:
        # 한글을 유니코드 이스케이프하지 않고 들여쓰기하여 JSON을 저장합니다.
        json.dump(
            json_data,
            json_file,
            ensure_ascii=False,
            indent=2,
        )

    # 생성된 TXT와 JSON 경로를 사전으로 반환합니다.
    return {
        "text": text_path,
        "json": json_path,
    }
