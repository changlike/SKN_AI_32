"""이미지 생성과 STT API 요청 및 응답 모델을 정의합니다."""

# 입력값 검증 기능을 사용하기 위해 BaseModel과 Field를 가져옵니다.
from pydantic import BaseModel, Field


# 이미지 생성 요청 JSON 구조를 정의합니다.
class ImageGenerationRequest(BaseModel):
    """프롬프트와 Stable Diffusion 추론 옵션을 전달받습니다."""

    # 생성할 이미지 내용을 설명하는 필수 프롬프트를 정의합니다.
    prompt: str = Field(..., min_length=1, max_length=2000)

    # 이미지에서 제외할 요소를 설명하는 선택 프롬프트를 정의합니다.
    negative_prompt: str = Field(
        default=(
            "low quality, blurry, distorted, deformed, bad anatomy, "
            "watermark, text, logo"
        ),
        max_length=2000,
    )

    # 노이즈 제거 반복 횟수를 제한합니다.
    inference_steps: int = Field(default=25, ge=1, le=100)

    # 프롬프트 반영 강도를 제한합니다.
    guidance_scale: float = Field(default=7.5, ge=0.0, le=20.0)

    # 생성 이미지 가로 크기를 제한합니다.
    width: int = Field(default=512, ge=256, le=1024)

    # 생성 이미지 세로 크기를 제한합니다.
    height: int = Field(default=512, ge=256, le=1024)

    # 중간 이미지 저장 단계 간격을 제한합니다.
    save_interval: int = Field(default=5, ge=1, le=50)

    # 동일 결과를 재현할 선택 시드를 정의합니다.
    seed: int | None = Field(default=None, ge=0, le=2_147_483_647)


# 이미지 생성 작업 접수 응답 구조를 정의합니다.
class ImageGenerationAcceptedResponse(BaseModel):
    """비동기 생성 작업의 ID와 실제 시드를 반환합니다."""

    # 상태 조회에 사용할 작업 ID를 정의합니다.
    job_id: str

    # 접수 직후 상태를 정의합니다.
    status: str

    # 실제 이미지 생성에 사용할 시드를 정의합니다.
    seed: int


# STT 변환 응답 구조를 정의합니다.
class TranscriptionResponse(BaseModel):
    """저장된 음성과 변환 텍스트 정보를 반환합니다."""

    # 서버가 생성한 녹음 ID를 정의합니다.
    recording_id: str

    # 저장된 음성 파일 URL을 정의합니다.
    audio_url: str

    # 저장된 STT 텍스트 파일 URL을 정의합니다.
    transcript_url: str

    # 음성에서 변환한 문장을 정의합니다.
    text: str
