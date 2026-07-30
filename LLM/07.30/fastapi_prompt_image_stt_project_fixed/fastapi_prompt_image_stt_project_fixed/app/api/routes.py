"""메인 페이지, STT, 이미지 생성과 작업 상태 조회 API를 정의합니다."""

# FastAPI 라우터, 백그라운드 작업, 파일 업로드와 오류 기능을 가져옵니다.
from fastapi import APIRouter, BackgroundTasks, File, HTTPException, Request, UploadFile

# Jinja2 HTML 템플릿 응답 기능을 가져옵니다.
from fastapi.templating import Jinja2Templates

# 작업 고유 ID를 생성하기 위해 uuid4를 가져옵니다.
from uuid import uuid4

# 공통 설정을 가져옵니다.
from app.core.config import settings

# API 요청과 응답 모델을 가져옵니다.
from app.schemas.generation import (
    ImageGenerationAcceptedResponse,
    ImageGenerationRequest,
    TranscriptionResponse,
)

# 이미지 생성 서비스 함수를 가져옵니다.
from app.services.image_service import (
    create_random_seed,
    run_generation_job,
    validate_dimensions,
)

# 작업 상태 관리자를 가져옵니다.
from app.services.job_manager import job_manager

# 음성 저장 및 STT 변환 함수를 가져옵니다.
from app.services.stt_service import save_and_transcribe_audio


# 엔드포인트를 묶는 라우터를 생성합니다.
router = APIRouter()

# HTML 템플릿 디렉터리를 사용하는 렌더링 객체를 생성합니다.
templates = Jinja2Templates(directory=str(settings.templates_dir))


# 첫 화면을 반환하는 엔드포인트를 정의합니다.
@router.get("/")
async def read_index(request: Request):
    """프롬프트 이미지 생성 프론트 페이지를 반환합니다."""

    # HTML 템플릿에 기본 옵션과 모델 ID를 전달합니다.
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "app_name": settings.app_name,
            "model_id": settings.image_model_id,
            "default_steps": settings.default_inference_steps,
            "default_guidance": settings.default_guidance_scale,
            "default_width": settings.default_width,
            "default_height": settings.default_height,
            "default_save_interval": settings.default_save_interval,
        },
    )


# 서버 상태 확인 API를 정의합니다.
@router.get("/api/health")
async def health_check() -> dict[str, str]:
    """서버 상태와 이미지 모델 ID를 반환합니다."""

    # 정상 상태 정보를 JSON으로 반환합니다.
    return {
        "status": "ok",
        "application": settings.app_name,
        "model_id": settings.image_model_id,
    }


# 음성 파일을 저장하고 STT로 변환하는 API를 정의합니다.
@router.post("/api/stt/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(audio: UploadFile = File(...)) -> TranscriptionResponse:
    """브라우저 녹음 파일을 텍스트 프롬프트로 변환합니다."""

    # 업로드 파일의 MIME 타입을 가져옵니다.
    content_type = audio.content_type or ""

    # 음성 또는 브라우저 녹음 형식인지 확인합니다.
    if not (
        content_type.startswith("audio/")
        or content_type.startswith("video/")
        or content_type == "application/octet-stream"
    ):
        # 지원하지 않는 형식이면 400 오류를 반환합니다.
        raise HTTPException(
            status_code=400,
            detail=f"지원하지 않는 음성 형식입니다: {content_type}",
        )

    # 입력 오류와 서버 오류를 구분하여 처리합니다.
    try:
        # 음성을 저장하고 STT 변환을 수행합니다.
        result = await save_and_transcribe_audio(audio)

        # 변환 결과를 응답 모델로 반환합니다.
        return TranscriptionResponse(**result)
    except ValueError as error:
        # 인식 실패와 같은 사용자 입력 오류를 400으로 반환합니다.
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        # 모델 로딩 또는 디코딩 오류를 500으로 반환합니다.
        raise HTTPException(
            status_code=500,
            detail=f"STT 처리 오류: {type(error).__name__}: {error}",
        ) from error


# 프롬프트 기반 이미지 생성 작업을 접수합니다.
@router.post(
    "/api/generations",
    response_model=ImageGenerationAcceptedResponse,
    status_code=202,
)
async def create_generation(
    request_data: ImageGenerationRequest,
    background_tasks: BackgroundTasks,
) -> ImageGenerationAcceptedResponse:
    """Stable Diffusion 생성 작업을 백그라운드에 등록합니다."""

    # 이미지 크기 규칙을 검증합니다.
    try:
        validate_dimensions(request_data.width, request_data.height)
    except ValueError as error:
        # 잘못된 크기를 422 입력 오류로 반환합니다.
        raise HTTPException(status_code=422, detail=str(error)) from error

    # 시드가 없으면 무작위 시드를 생성합니다.
    seed = request_data.seed if request_data.seed is not None else create_random_seed()

    # 상태 조회용 작업 ID를 생성합니다.
    job_id = uuid4().hex

    # 작업의 초기 상태와 입력 옵션을 저장합니다.
    job_manager.create(
        job_id,
        {
            "job_id": job_id,
            "model_id": settings.image_model_id,
            "status": "queued",
            "message": "이미지 생성 작업이 대기열에 등록되었습니다.",
            "progress": 0,
            "prompt": request_data.prompt,
            "negative_prompt": request_data.negative_prompt,
            "inference_steps": request_data.inference_steps,
            "guidance_scale": request_data.guidance_scale,
            "width": request_data.width,
            "height": request_data.height,
            "save_interval": request_data.save_interval,
            "seed": seed,
            "current_step": 0,
            "step_images": [],
            "final_image_url": None,
            "metadata_url": None,
            "cleaned_prompt": None,
            "translated_prompt": None,
            "enhanced_prompt": None,
            "final_negative_prompt": None,
            "korean_detected": None,
        },
    )

    # HTTP 응답 후 실행할 이미지 생성 작업을 등록합니다.
    background_tasks.add_task(
        run_generation_job,
        job_id,
        request_data.prompt,
        request_data.negative_prompt,
        request_data.inference_steps,
        request_data.guidance_scale,
        request_data.width,
        request_data.height,
        request_data.save_interval,
        seed,
    )

    # 프론트가 상태 조회를 시작할 수 있도록 작업 정보를 반환합니다.
    return ImageGenerationAcceptedResponse(
        job_id=job_id,
        status="queued",
        seed=seed,
    )


# 작업 진행 상태를 조회하는 API를 정의합니다.
@router.get("/api/generations/{job_id}")
async def get_generation(job_id: str) -> dict:
    """진행률, 중간 이미지와 최종 결과를 반환합니다."""

    # 작업 상태 저장소에서 ID를 조회합니다.
    job = job_manager.get(job_id)

    # 존재하지 않는 작업인지 확인합니다.
    if job is None:
        # 존재하지 않으면 404 오류를 반환합니다.
        raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다.")

    # 현재 작업 상태를 반환합니다.
    return job
