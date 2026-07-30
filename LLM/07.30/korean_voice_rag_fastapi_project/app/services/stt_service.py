"""Faster-Whisper를 이용해 브라우저 녹음 파일을 한국어 텍스트로 변환합니다."""
from pathlib import Path  # 업로드 음성 파일 경로를 처리합니다.
from threading import Lock  # Whisper 모델 중복 로딩을 방지합니다.
from app.config import settings  # STT 모델 설정을 가져옵니다.

class SpeechToTextService:
    """WEBM, WAV, MP3, M4A, OGG, FLAC 음성을 한국어로 인식합니다."""
    def __init__(self) -> None:
        self._model = None  # Faster-Whisper 모델을 최초 요청 시 저장합니다.
        self._lock = Lock()  # 최초 모델 로딩 구간을 보호합니다.
        self._device_name = "not_loaded"  # 상태 API에 표시할 장치 이름입니다.
        self._compute_type = "not_loaded"  # 상태 API에 표시할 계산 형식입니다.

    def _device(self) -> str:
        if settings.WHISPER_DEVICE in {"cpu", "cuda"}:
            return settings.WHISPER_DEVICE  # 사용자가 명시한 장치를 사용합니다.
        try:
            import torch  # CUDA 사용 가능 여부를 확인합니다.
            return "cuda" if torch.cuda.is_available() else "cpu"  # GPU가 있으면 CUDA, 없으면 CPU를 선택합니다.
        except Exception:
            return "cpu"  # PyTorch가 없거나 확인에 실패하면 CPU를 사용합니다.

    def _get_model(self):
        if self._model is not None:
            return self._model  # 이미 로딩된 모델을 재사용합니다.
        with self._lock:
            if self._model is None:
                from faster_whisper import WhisperModel  # 실제 STT 요청이 들어올 때 패키지를 가져옵니다.
                device = self._device()  # 실행 장치를 결정합니다.
                requested = settings.WHISPER_COMPUTE_TYPE  # 사용자가 지정한 계산 형식을 읽습니다.
                compute_type = "float16" if device == "cuda" and requested in {"int8", "auto"} else requested  # GPU 기본값을 float16으로 보정합니다.
                if device == "cpu" and compute_type in {"float16", "auto"}:
                    compute_type = "int8"  # CPU에서 지원되지 않는 float16을 int8로 보정합니다.
                self._model = WhisperModel(settings.WHISPER_MODEL_SIZE, device=device, compute_type=compute_type)  # Whisper 모델을 생성합니다.
                self._device_name = device  # 실제 장치를 상태에 저장합니다.
                self._compute_type = compute_type  # 실제 계산 형식을 상태에 저장합니다.
        return self._model  # 준비된 모델을 반환합니다.

    def transcribe(self, audio_path: Path) -> str:
        if not audio_path.is_file():
            raise FileNotFoundError(f"음성 파일을 찾을 수 없습니다: {audio_path}")  # 저장 실패나 잘못된 경로를 명확히 알립니다.
        if audio_path.stat().st_size < 1024:
            raise ValueError("녹음 파일이 너무 작습니다. 1초 이상 말한 뒤 다시 시도해 주세요.")  # 지나치게 짧은 녹음을 거부합니다.
        try:
            segments, _ = self._get_model().transcribe(str(audio_path), language="ko", task="transcribe", vad_filter=True, vad_parameters={"min_silence_duration_ms": 400}, beam_size=5, condition_on_previous_text=False)  # 한국어 인식과 무음 제거를 수행합니다.
            text = " ".join(segment.text.strip() for segment in segments if segment.text.strip()).strip()  # 여러 음성 구간을 한 문장으로 결합합니다.
        except Exception as exc:
            message = str(exc)  # 원본 오류 메시지를 문자열로 변환합니다.
            if "ffmpeg" in message.lower() or "avcodec" in message.lower() or "decode" in message.lower():
                raise RuntimeError("음성 파일을 디코딩하지 못했습니다. FFmpeg 설치와 브라우저 녹음 형식을 확인해 주세요.") from exc  # 디코더 오류를 이해하기 쉬운 문장으로 변환합니다.
            raise RuntimeError(f"Whisper 음성 인식 실패: {type(exc).__name__}: {exc}") from exc  # 그 외 모델 오류는 형식과 원인을 함께 전달합니다.
        if not text:
            raise ValueError("음성을 인식하지 못했습니다. 마이크 권한과 입력 음량을 확인하고 다시 말해 주세요.")  # 무음 또는 인식 실패를 안내합니다.
        return text  # 정상 인식된 UTF-8 한국어 문자열을 반환합니다.

    def status(self) -> dict:
        return {"model_size": settings.WHISPER_MODEL_SIZE, "device": self._device_name, "compute_type": self._compute_type}  # STT 설정과 실제 로딩 상태를 반환합니다.
