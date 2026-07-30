"""한국어 답변을 음성 파일로 변환합니다."""
import asyncio  # 동기 TTS 대체 함수를 스레드에서 실행합니다.
import uuid  # 충돌 없는 파일명을 생성합니다.
from app.config import settings  # TTS 설정과 저장 경로를 가져옵니다.

class TextToSpeechService:
    """Edge TTS를 우선 사용하고 pyttsx3로 대체합니다."""
    async def synthesize(self, text: str) -> str:
        settings.AUDIO_DIR.mkdir(parents=True, exist_ok=True)  # 음성 저장 디렉터리를 보장합니다.
        file_id = uuid.uuid4().hex  # 고유 파일 식별자를 생성합니다.
        if settings.TTS_PROVIDER.lower() == 'edge':  # 네트워크 기반 Edge TTS를 선택했는지 확인합니다.
            try:
                import edge_tts  # 한국어 Neural Voice 패키지를 가져옵니다.
                path = settings.AUDIO_DIR / f'{file_id}.mp3'  # MP3 저장 경로를 만듭니다.
                communicate = edge_tts.Communicate(text=text, voice=settings.EDGE_TTS_VOICE, rate=settings.EDGE_TTS_RATE)  # 합성 요청 객체를 생성합니다.
                await communicate.save(str(path))  # MP3 파일을 비동기로 저장합니다.
                return f'/generated-audio/{path.name}'  # 브라우저 접근 URL을 반환합니다.
            except Exception:
                pass  # Edge TTS 실패 시 아래 오프라인 방식으로 전환합니다.
        path = settings.AUDIO_DIR / f'{file_id}.wav'  # 대체 WAV 경로를 만듭니다.
        await asyncio.to_thread(self._pyttsx3, text, path)  # 이벤트 루프를 막지 않도록 별도 스레드에서 합성합니다.
        return f'/generated-audio/{path.name}'  # WAV 접근 URL을 반환합니다.

    def _pyttsx3(self, text, path) -> None:
        import pyttsx3  # 운영체제 음성 엔진 패키지를 가져옵니다.
        engine = pyttsx3.init()  # 현재 OS의 음성 엔진을 초기화합니다.
        for voice in engine.getProperty('voices'):  # 설치된 음성을 순회합니다.
            info = f"{getattr(voice,'name','')} {getattr(voice,'id','')} {getattr(voice,'languages','')}".lower()  # 검색 가능한 문자열을 구성합니다.
            if 'ko' in info or 'korean' in info or '한국' in info:  # 한국어 음성을 찾습니다.
                engine.setProperty('voice', voice.id)  # 한국어 음성 ID를 적용합니다.
                break
        engine.setProperty('rate', 175)  # 자연스러운 발화 속도를 설정합니다.
        engine.save_to_file(text, str(path))  # 합성 결과를 파일로 예약합니다.
        engine.runAndWait()  # 파일 저장이 완료될 때까지 실행합니다.
