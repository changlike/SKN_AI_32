"""FastAPI 한국어 음성 RAG 서비스 진입점입니다."""
import asyncio  # 모델의 동기 추론을 별도 스레드에서 실행합니다.
import uuid  # 업로드 파일명을 고유하게 만듭니다.
import logging  # 처리 단계별 오류 원인을 서버 터미널에 기록합니다.
from pathlib import Path  # 업로드 확장자를 처리합니다.
from fastapi import FastAPI, File, HTTPException, UploadFile  # API와 파일 업로드 기능을 가져옵니다.
from fastapi.responses import FileResponse  # 웹 메인 파일을 반환합니다.
from fastapi.staticfiles import StaticFiles  # 정적 파일과 음성 파일을 제공합니다.
from app.config import settings  # 프로젝트 설정을 가져옵니다.
from app.schemas import AskResponse, SourceItem, TextQuestionRequest  # 검증된 입출력 모델을 가져옵니다.
from app.services.stt_service import SpeechToTextService  # 한국어 STT 서비스를 가져옵니다.
from app.services.rag_service import RagService  # 문서 검색 서비스를 가져옵니다.
from app.services.llm_service import FineTunedLlmService  # 파인튜닝 LLM 서비스를 가져옵니다.
from app.services.tts_service import TextToSpeechService  # 한국어 TTS 서비스를 가져옵니다.

logger = logging.getLogger(__name__)  # 현재 모듈 전용 로거를 생성합니다.

for directory in (settings.UPLOAD_DIR, settings.AUDIO_DIR, settings.DOCUMENT_DIR): directory.mkdir(parents=True, exist_ok=True)  # 실행 디렉터리를 생성합니다.
app = FastAPI(title=settings.APP_NAME, description='한국어 STT → RAG → 파인튜닝 LLM → TTS', version='1.0.0')  # API 애플리케이션을 생성합니다.
app.mount('/static', StaticFiles(directory=str(settings.STATIC_DIR)), name='static')  # CSS와 JS를 연결합니다.
app.mount('/generated-audio', StaticFiles(directory=str(settings.AUDIO_DIR)), name='generated-audio')  # 생성 음성을 연결합니다.
stt, rag, llm, tts = SpeechToTextService(), RagService(), FineTunedLlmService(), TextToSpeechService()  # 무거운 모델을 공유할 서비스 객체를 생성합니다.

async def process(question: str, speak: bool) -> AskResponse:
    question = question.strip()  # 질문 앞뒤 공백을 제거합니다.
    if not question: raise HTTPException(400, '질문이 비어 있습니다.')  # 빈 질문을 거부합니다.
    contexts = await asyncio.to_thread(rag.search, question)  # 의미 검색을 별도 스레드에서 실행합니다.
    answer = await asyncio.to_thread(llm.generate, question, contexts)  # LLM 추론을 별도 스레드에서 실행합니다.
    audio_url = None  # TTS가 실패해도 텍스트 답변은 정상 반환하도록 기본값을 지정합니다.
    if speak:  # 사용자가 음성 자동 재생을 요청했는지 확인합니다.
        try:
            audio_url = await tts.synthesize(answer)  # 생성된 답변을 한국어 음성 파일로 변환합니다.
        except Exception as exc:
            logger.exception("TTS 생성 실패 - 텍스트 답변만 반환합니다: %s", exc)  # TTS 오류를 기록하되 API 전체를 500으로 중단하지 않습니다.
    sources = [SourceItem(source=c['source'], page=c.get('page'), chunk_id=c['chunk_id'], score=round(c['score'],4), preview=c['text'][:320]) for c in contexts]  # 검색 결과를 응답 구조로 변환합니다.
    return AskResponse(question=question, answer=answer, sources=sources, audio_url=audio_url, model_mode=llm.mode)  # 최종 결과를 반환합니다.

@app.get('/', include_in_schema=False)
async def home():
    return FileResponse(settings.STATIC_DIR / 'index.html')  # 사용자 웹 화면을 반환합니다.

@app.get('/api/health')
async def health():
    return {'status':'ok','llm_mode':llm.mode,'llm_load_error':llm.load_error,'use_local_model':settings.USE_LOCAL_MODEL,'local_model_path':str(settings.LOCAL_MODEL_PATH),'rag':await asyncio.to_thread(rag.status),'stt':stt.status(),'embedding_model':settings.EMBEDDING_MODEL_NAME,'tts_provider':settings.TTS_PROVIDER}  # 주요 상태와 모델 경로 및 마지막 로딩 오류를 반환합니다.

@app.post('/api/ask/text', response_model=AskResponse)
async def ask_text(payload: TextQuestionRequest):
    return await process(payload.question, payload.speak)  # 텍스트 질문을 공통 파이프라인에 전달합니다.

@app.post('/api/ask/voice', response_model=AskResponse)
async def ask_voice(audio: UploadFile = File(...), speak: bool = True):
    suffix = Path(audio.filename or 'recording.webm').suffix.lower()  # 원본 확장자를 읽습니다.
    if suffix not in {'.webm','.wav','.mp3','.m4a','.ogg','.flac'}: suffix = '.webm'  # 안전한 확장자로 제한합니다.
    path = settings.UPLOAD_DIR / f'{uuid.uuid4().hex}{suffix}'  # 고유 저장 경로를 생성합니다.
    try:
        content = await audio.read()  # 업로드 파일을 비동기로 읽습니다.
        if not content: raise HTTPException(400, '음성 파일이 비어 있습니다.')  # 빈 파일을 거부합니다.
        if len(content) > 25 * 1024 * 1024: raise HTTPException(413, '음성 파일은 25MB 이하여야 합니다.')  # 파일 크기를 제한합니다.
        path.write_bytes(content)  # 녹음 파일을 서버에 저장합니다.
        question = await asyncio.to_thread(stt.transcribe, path)  # 한국어 STT를 실행합니다.
        return await process(question, speak)  # 인식된 질문을 RAG 파이프라인에 전달합니다.
    except HTTPException:
        raise  # 의미 있는 HTTP 상태를 유지합니다.
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc  # 무음이나 너무 짧은 녹음은 사용자가 수정할 수 있는 400 오류로 반환합니다.
    except Exception as exc:
        logger.exception('음성 질문 처리 실패: %s', exc)  # 서버 터미널에 상세 오류를 기록합니다.
        raise HTTPException(500, f'음성 질문 처리 오류: {exc}') from exc  # 모델 및 디코딩 오류를 설명합니다.
    finally:
        await audio.close()  # 업로드 파일 핸들을 닫습니다.

@app.post('/api/rag/rebuild')
async def rebuild():
    count = await asyncio.to_thread(rag.rebuild)  # 문서 인덱스를 새로 생성합니다.
    return {'message':'RAG 인덱스 재생성 완료','chunk_count':count}  # 새 조각 수를 반환합니다.
