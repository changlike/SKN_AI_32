"""
SDXL을 사용하여 번역 및 보강된 프롬프트 기반 이미지를 생성합니다.
"""

# 생성 작업 메타데이터를 JSON 파일로 저장하기 위해 json 모듈을 가져옵니다.
import json

# 하나의 로컬 이미지 모델에 여러 작업이 동시에 접근하지 못하도록 Lock을 가져옵니다.
from threading import Lock

# 사용자가 시드를 입력하지 않았을 때 안전한 무작위 시드를 생성하기 위해 secrets를 가져옵니다.
import secrets

# 지연 로딩 파이프라인 객체에 유연한 타입을 적용하기 위해 Any를 가져옵니다.
from typing import Any

# 장치, 데이터 타입과 난수 생성기를 사용하기 위해 torch를 가져옵니다.
import torch

# 프로젝트 환경 설정 객체를 가져옵니다.
from app.core.config import settings

# 작업 상태를 갱신하기 위해 job_manager를 가져옵니다.
from app.services.job_manager import job_manager

# 한국어 프롬프트 번역 및 자동 보강 함수를 가져옵니다.
from app.services.prompt_service import prepare_prompt


# 텍스트-이미지 파이프라인을 최초 한 번만 로딩하기 위한 캐시 변수를 선언합니다.
_pipeline: Any | None = None

# 최초 모델 로딩의 동시 실행을 막는 잠금 객체를 생성합니다.
_pipeline_load_lock = Lock()

# 하나의 GPU 또는 CPU에서 이미지 생성 작업을 순차 실행하기 위한 잠금 객체를 생성합니다.
_generation_lock = Lock()


# 사용자가 시드를 지정하지 않았을 때 사용할 난수를 생성합니다.
def create_random_seed() -> int:
    """PyTorch가 사용할 수 있는 31비트 양의 정수 시드를 반환합니다."""

    # 0 이상 2^31 미만의 안전한 난수를 생성하여 반환합니다.
    return secrets.randbelow(2_147_483_648)


# 생성 이미지 크기가 디퓨전 모델 요구조건에 맞는지 검증합니다.
def validate_dimensions(width: int, height: int) -> None:
    """가로와 세로 크기가 모두 8의 배수인지 확인합니다."""

    # 가로 또는 세로가 8의 배수가 아닌지 확인합니다.
    if width % 8 != 0 or height % 8 != 0:
        # 잠재 공간 크기를 계산할 수 없으므로 오류를 발생시킵니다.
        raise ValueError("이미지 가로와 세로 크기는 모두 8의 배수여야 합니다.")


# 현재 환경에 적합한 SDXL 파이프라인을 로딩합니다.
def get_image_pipeline() -> Any:
    """이미지 모델을 최초 생성 요청 때 로딩하고 이후 요청에서 재사용합니다."""

    # 함수 내부에서 전역 파이프라인 캐시를 수정하겠다고 선언합니다.
    global _pipeline

    # 파이프라인이 이미 생성되어 있는지 확인합니다.
    if _pipeline is not None:
        # 기존 파이프라인을 즉시 반환합니다.
        return _pipeline

    # 여러 요청이 동시에 모델을 내려받지 못하도록 잠금을 획득합니다.
    with _pipeline_load_lock:
        # 잠금을 기다리는 동안 모델 로딩이 완료되었는지 다시 확인합니다.
        if _pipeline is not None:
            # 이미 생성된 파이프라인을 반환합니다.
            return _pipeline

        # 서버 시작 시간을 줄이기 위해 실제 요청 시점에 Diffusers를 가져옵니다.
        from diffusers import AutoPipelineForText2Image, DPMSolverMultistepScheduler

        # CUDA GPU를 사용할 수 있는지 확인합니다.
        cuda_available = torch.cuda.is_available()

        # GPU에서는 float16을, CPU에서는 float32를 사용합니다.
        torch_dtype = torch.float16 if cuda_available else torch.float32

        # 설정된 Hugging Face 모델 ID로 텍스트-이미지 파이프라인을 로딩합니다.
        _pipeline = AutoPipelineForText2Image.from_pretrained(
            settings.image_model_id,
            torch_dtype=torch_dtype,
            use_safetensors=True,
        )

        # 기존 스케줄러 설정을 유지하면서 DPM-Solver++ 계열 스케줄러로 교체합니다.
        _pipeline.scheduler = DPMSolverMultistepScheduler.from_config(
            _pipeline.scheduler.config,
            algorithm_type="dpmsolver++",
            use_karras_sigmas=True,
        )

        # CUDA GPU를 사용할 수 있는지 확인합니다.
        if cuda_available:
            # CPU 오프로딩 옵션이 활성화되어 있는지 확인합니다.
            if settings.enable_cpu_offload:
                # 사용 중인 모듈만 GPU로 이동하여 VRAM 사용량을 줄입니다.
                _pipeline.enable_model_cpu_offload()
            else:
                # 전체 파이프라인을 CUDA 장치로 이동합니다.
                _pipeline.to("cuda")
        else:
            # GPU가 없으면 전체 파이프라인을 CPU로 이동합니다.
            _pipeline.to("cpu")

        # VAE slicing 옵션이 활성화되어 있는지 확인합니다.
        if settings.enable_vae_slicing:
            # VAE 디코딩을 나누어 수행하여 메모리 사용량을 줄입니다.
            _pipeline.enable_vae_slicing()

        # VAE tiling 옵션이 활성화되어 있는지 확인합니다.
        if settings.enable_vae_tiling:
            # 큰 이미지를 타일 단위로 디코딩하여 메모리 사용량을 줄입니다.
            _pipeline.enable_vae_tiling()

        # Attention slicing 옵션이 활성화되어 있는지 확인합니다.
        if settings.enable_attention_slicing:
            # Attention 계산을 나누어 수행하여 메모리 사용량을 줄입니다.
            _pipeline.enable_attention_slicing()

        # 완성된 이미지 생성 파이프라인을 반환합니다.
        return _pipeline


# 현재 잠재 텐서를 중간 확인용 PIL 이미지로 변환합니다.
def decode_latents_to_pil(
    pipeline: Any,
    latents: torch.Tensor,
):
    """현재 디퓨전 잠재 텐서의 첫 번째 이미지를 RGB PIL 이미지로 변환합니다."""

    # VAE 설정에 저장된 잠재 공간 크기 보정 계수를 가져옵니다.
    scaling_factor = pipeline.vae.config.scaling_factor

    # VAE가 요구하는 크기로 잠재값을 복원합니다.
    scaled_latents = latents / scaling_factor

    # 중간 확인 이미지에는 역전파가 필요 없으므로 기울기 계산을 끕니다.
    with torch.no_grad():
        # VAE 디코더를 이용해 잠재 텐서를 픽셀 공간 텐서로 변환합니다.
        decoded = pipeline.vae.decode(
            scaled_latents,
            return_dict=False,
        )[0]

    # 파이프라인 이미지 후처리기로 첫 번째 텐서를 PIL 이미지로 변환합니다.
    image = pipeline.image_processor.postprocess(
        decoded,
        output_type="pil",
    )[0]

    # 변환된 RGB 이미지를 반환합니다.
    return image.convert("RGB")


# 실제 프롬프트 기반 이미지 생성 작업을 수행합니다.
def run_generation_job(
    job_id: str,
    prompt: str,
    negative_prompt: str,
    inference_steps: int,
    guidance_scale: float,
    width: int,
    height: int,
    save_interval: int,
    seed: int,
) -> None:
    """한국어 번역, 프롬프트 보강, SDXL 추론과 단계별 저장을 수행합니다."""

    # 모든 오류를 작업 상태로 전달하기 위해 전체 로직을 try 블록으로 감쌉니다.
    try:
        # 이미지 크기가 모델 요구사항에 맞는지 확인합니다.
        validate_dimensions(width, height)

        # 작업별 이미지와 메타데이터 저장 디렉터리를 생성합니다.
        job_directory = settings.generation_dir / job_id

        # 작업 디렉터리가 없으면 상위 경로까지 포함하여 생성합니다.
        job_directory.mkdir(parents=True, exist_ok=True)

        # 현재 상태를 프롬프트 분석 단계로 변경합니다.
        job_manager.update(
            job_id,
            status="preparing_prompt",
            message="한국어 프롬프트를 분석하고 이미지 생성용 문장으로 변환합니다.",
            progress=1,
        )

        # 한국어 자동 번역, 핵심 장면 보강과 Negative prompt 보정을 수행합니다.
        prompt_data = prepare_prompt(
            original_prompt=prompt,
            user_negative_prompt=negative_prompt,
        )

        # 실제 이미지 모델에 전달할 보강 프롬프트를 가져옵니다.
        generation_prompt = str(prompt_data["enhanced_prompt"])

        # 실제 이미지 모델에 전달할 최종 Negative prompt를 가져옵니다.
        generation_negative_prompt = str(
            prompt_data["final_negative_prompt"]
        )

        # 번역 및 보강 결과를 프론트 상태에 즉시 반영합니다.
        job_manager.update(
            job_id,
            status="loading",
            message="번역된 프롬프트를 준비했습니다. SDXL 모델을 로딩합니다.",
            progress=4,
            cleaned_prompt=prompt_data["cleaned_prompt"],
            translated_prompt=prompt_data["translated_prompt"],
            enhanced_prompt=generation_prompt,
            final_negative_prompt=generation_negative_prompt,
            korean_detected=prompt_data["korean_detected"],
        )

        # 캐시되었거나 새로 로딩된 이미지 생성 파이프라인을 가져옵니다.
        pipeline = get_image_pipeline()

        # 파이프라인이 실제로 사용하는 실행 장치를 확인합니다.
        execution_device = pipeline._execution_device

        # 동일한 시드로 결과를 재현할 PyTorch 난수 생성기를 만듭니다.
        generator = torch.Generator(
            device=execution_device.type
        ).manual_seed(seed)

        # 단계별 저장 이미지 URL 목록을 초기화합니다.
        step_image_urls: list[str] = []

        # Diffusers가 각 노이즈 제거 단계 종료 후 호출할 함수를 정의합니다.
        def save_step_callback(
            pipe: Any,
            step_index: int,
            timestep: torch.Tensor,
            callback_kwargs: dict[str, torch.Tensor],
        ) -> dict[str, torch.Tensor]:
            """지정 간격마다 현재 잠재값을 디코딩하여 중간 PNG로 저장합니다."""

            # 사용자 화면에 표시할 단계 번호를 1부터 시작하도록 계산합니다.
            current_step = step_index + 1

            # 저장 간격에 해당하거나 마지막 단계인지 확인합니다.
            should_save = (
                current_step % save_interval == 0
                or current_step == inference_steps
            )

            # 현재 단계 이미지를 저장해야 하는지 확인합니다.
            if should_save:
                # 콜백 인수에서 현재 잠재 텐서를 가져옵니다.
                current_latents = callback_kwargs["latents"]

                # 현재 잠재 텐서를 확인 가능한 RGB 이미지로 변환합니다.
                intermediate_image = decode_latents_to_pil(
                    pipe,
                    current_latents,
                )

                # 현재 단계 번호를 포함한 파일명을 생성합니다.
                filename = f"step_{current_step:03d}.png"

                # 작업 디렉터리 아래의 전체 저장 경로를 생성합니다.
                output_path = job_directory / filename

                # 중간 이미지를 PNG 형식으로 저장합니다.
                intermediate_image.save(
                    output_path,
                    format="PNG",
                )

                # 브라우저가 접근할 수 있는 중간 이미지 URL을 생성합니다.
                image_url = (
                    f"{settings.storage_url_prefix}/generations/"
                    f"{job_id}/{filename}"
                )

                # 동일한 URL이 아직 목록에 없는지 확인합니다.
                if image_url not in step_image_urls:
                    # 새 중간 이미지 URL을 결과 목록에 추가합니다.
                    step_image_urls.append(image_url)

            # 현재 단계 비율을 이용하여 8~95 범위의 진행률을 계산합니다.
            progress = 8 + int(current_step / inference_steps * 87)

            # 프론트에 현재 단계와 중간 이미지 목록을 전달합니다.
            job_manager.update(
                job_id,
                status="running",
                message=(
                    f"{current_step}/{inference_steps} "
                    "노이즈 제거 단계를 처리하고 있습니다."
                ),
                current_step=current_step,
                progress=min(progress, 95),
                step_images=list(step_image_urls),
            )

            # 파이프라인이 다음 단계를 계속 수행하도록 콜백 인수를 반환합니다.
            return callback_kwargs

        # 한 번에 하나의 생성 작업만 모델에 접근하도록 잠금을 획득합니다.
        with _generation_lock:
            # 실제 이미지 생성 시작 상태를 프론트에 전달합니다.
            job_manager.update(
                job_id,
                status="running",
                message="번역 및 보강된 프롬프트로 SDXL 이미지를 생성합니다.",
                progress=8,
                device=str(execution_device),
            )

            # SDXL 파이프라인을 실행하여 최종 이미지를 생성합니다.
            result = pipeline(
                prompt=generation_prompt,
                negative_prompt=generation_negative_prompt,
                num_inference_steps=inference_steps,
                guidance_scale=guidance_scale,
                width=width,
                height=height,
                generator=generator,
                callback_on_step_end=save_step_callback,
                callback_on_step_end_tensor_inputs=["latents"],
            )

        # 파이프라인 결과의 첫 번째 이미지를 가져옵니다.
        final_image = result.images[0].convert("RGB")

        # 최종 이미지 파일명을 지정합니다.
        final_filename = "final.png"

        # 최종 이미지 전체 저장 경로를 생성합니다.
        final_path = job_directory / final_filename

        # 최종 이미지를 PNG 형식으로 저장합니다.
        final_image.save(
            final_path,
            format="PNG",
        )

        # 브라우저에서 접근 가능한 최종 이미지 URL을 생성합니다.
        final_image_url = (
            f"{settings.storage_url_prefix}/generations/"
            f"{job_id}/{final_filename}"
        )

        # 입력, 번역, 보강과 생성 설정을 메타데이터로 구성합니다.
        metadata = {
            "job_id": job_id,
            "model_id": settings.image_model_id,
            "original_prompt": prompt_data["original_prompt"],
            "cleaned_prompt": prompt_data["cleaned_prompt"],
            "translated_prompt": prompt_data["translated_prompt"],
            "enhanced_prompt": generation_prompt,
            "user_negative_prompt": negative_prompt,
            "final_negative_prompt": generation_negative_prompt,
            "korean_detected": prompt_data["korean_detected"],
            "inference_steps": inference_steps,
            "guidance_scale": guidance_scale,
            "width": width,
            "height": height,
            "save_interval": save_interval,
            "seed": seed,
            "device": str(execution_device),
            "step_images": step_image_urls,
            "final_image_url": final_image_url,
        }

        # 메타데이터를 한글이 유지되는 UTF-8 JSON 파일로 저장합니다.
        (job_directory / "metadata.json").write_text(
            json.dumps(
                metadata,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        # 브라우저에서 접근 가능한 메타데이터 URL을 생성합니다.
        metadata_url = (
            f"{settings.storage_url_prefix}/generations/"
            f"{job_id}/metadata.json"
        )

        # 작업 상태를 완료로 변경하고 모든 최종 정보를 저장합니다.
        job_manager.update(
            job_id,
            status="completed",
            message="한국어 프롬프트 요구에 맞는 이미지 생성을 완료했습니다.",
            progress=100,
            current_step=inference_steps,
            step_images=list(step_image_urls),
            final_image_url=final_image_url,
            metadata_url=metadata_url,
            translated_prompt=prompt_data["translated_prompt"],
            enhanced_prompt=generation_prompt,
            final_negative_prompt=generation_negative_prompt,
        )

        # CUDA GPU를 사용할 수 있는지 확인합니다.
        if torch.cuda.is_available():
            # 다음 요청을 위해 사용하지 않는 CUDA 캐시 메모리를 정리합니다.
            torch.cuda.empty_cache()

    # 번역, 모델 로딩, 추론 또는 저장 과정의 모든 오류를 처리합니다.
    except Exception as error:
        # 오류 타입과 내용을 작업 상태에 저장합니다.
        job_manager.update(
            job_id,
            status="failed",
            message=f"{type(error).__name__}: {error}",
            error=str(error),
        )

        # CUDA GPU를 사용할 수 있는지 확인합니다.
        if torch.cuda.is_available():
            # 오류 후 남아 있을 수 있는 CUDA 캐시를 정리합니다.
            torch.cuda.empty_cache()


# 이전 함수명을 사용하는 외부 코드와의 호환성을 유지합니다.
run_image_generation_job = run_generation_job
