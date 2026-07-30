"""브라우저 음성을 저장하고 faster-whisper로 텍스트를 변환합니다."""

from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import UploadFile
import torch

from app.core.config import settings

_whisper_model: Any | None = None


def get_whisper_model() -> Any:
    """Whisper 모델을 최초 요청에서 한 번만 로딩하고 이후 재사용합니다."""
    global _whisper_model
    if _whisper_model is not None:
        return _whisper_model

    from faster_whisper import WhisperModel

    selected_device = (
        "cuda" if torch.cuda.is_available() else "cpu"
    ) if settings.whisper_device == "auto" else settings.whisper_device

    compute_type = (
        settings.whisper_compute_type_cuda
        if selected_device == "cuda"
        else settings.whisper_compute_type_cpu
    )

    _whisper_model = WhisperModel(
        settings.whisper_model_size,
        device=selected_device,
        compute_type=compute_type,
    )
    return _whisper_model


def determine_extension(upload_file: UploadFile) -> str:
    """파일명과 MIME 타입을 함께 사용하여 안전한 확장자를 결정합니다."""
    suffix = Path(upload_file.filename or "").suffix.lower()
    allowed = {".webm", ".wav", ".mp3", ".m4a", ".ogg", ".mp4"}
    if suffix in allowed:
        return suffix

    content_type = (upload_file.content_type or "").lower()
    if "ogg" in content_type:
        return ".ogg"
    if "mp4" in content_type or "m4a" in content_type:
        return ".m4a"
    if "wav" in content_type:
        return ".wav"
    return ".webm"


def _segments_to_text(segments: Any) -> str:
    """Whisper 세그먼트 반복자를 끝까지 소비하여 한 문장으로 합칩니다."""
    return " ".join(
        segment.text.strip()
        for segment in segments
        if segment.text and segment.text.strip()
    ).strip()


def _transcribe_with_fallback(model: Any, audio_path: Path) -> tuple[str, Any, str]:
    """VAD 방식이 짧은 음성을 제거하면 VAD 없이 한 번 더 인식합니다."""
    common_options = {
        "language": settings.whisper_language or None,
        "beam_size": 5,
        "condition_on_previous_text": False,
        "initial_prompt": "한국어 이미지 생성 프롬프트입니다.",
    }

    # 일반적인 녹음에서는 VAD를 사용하여 긴 무음 구간을 제거합니다.
    segments, info = model.transcribe(
        str(audio_path),
        vad_filter=True,
        vad_parameters={"min_silence_duration_ms": 500},
        **common_options,
    )
    text = _segments_to_text(segments)
    if text:
        return text, info, "vad"

    # 짧은 발화가 VAD에서 모두 제거된 경우 VAD를 끄고 재시도합니다.
    segments, info = model.transcribe(
        str(audio_path),
        vad_filter=False,
        no_speech_threshold=0.8,
        log_prob_threshold=-2.0,
        compression_ratio_threshold=2.8,
        **common_options,
    )
    return _segments_to_text(segments), info, "fallback_no_vad"


async def save_and_transcribe_audio(upload_file: UploadFile) -> dict[str, str]:
    """음성 파일과 STT 결과를 저장하고 접근 URL을 반환합니다."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    recording_id = f"{timestamp}_{uuid4().hex[:8]}"
    extension = determine_extension(upload_file)
    audio_path = settings.audio_dir / f"{recording_id}{extension}"

    audio_bytes = await upload_file.read()
    if not audio_bytes:
        raise ValueError("업로드된 음성 데이터가 비어 있습니다.")
    if len(audio_bytes) < 1000:
        raise ValueError("녹음 파일이 너무 작습니다. 마이크를 누른 뒤 2초 이상 또렷하게 말해 주세요.")

    audio_path.write_bytes(audio_bytes)

    try:
        model = get_whisper_model()
        text, info, recognition_mode = _transcribe_with_fallback(model, audio_path)
    except Exception as error:
        raise RuntimeError(
            f"녹음 파일을 해석하지 못했습니다. 형식={upload_file.content_type}, "
            f"크기={len(audio_bytes)} bytes, 원인={type(error).__name__}: {error}"
        ) from error

    if not text:
        raise ValueError(
            "음성을 인식하지 못했습니다. 마이크 가까이에서 2초 이상 말한 뒤 다시 눌러 주세요. "
            "Windows 입력 장치와 Chrome 마이크 권한도 확인해 주세요."
        )

    transcript_path = settings.transcript_dir / f"{recording_id}.txt"
    transcript_path.write_text(
        (
            f"detected_language={info.language}\n"
            f"language_probability={info.language_probability:.4f}\n"
            f"recognition_mode={recognition_mode}\n"
            f"content_type={upload_file.content_type}\n"
            f"audio_bytes={len(audio_bytes)}\n"
            f"text={text}\n"
        ),
        encoding="utf-8-sig",
    )

    return {
        "recording_id": recording_id,
        "audio_url": f"{settings.storage_url_prefix}/audio/{audio_path.name}",
        "transcript_url": f"{settings.storage_url_prefix}/transcripts/{transcript_path.name}",
        "text": text,
    }
