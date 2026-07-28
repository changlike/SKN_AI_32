"""DPO Adapter 모델을 호출하는 FastAPI 추론 서비스입니다."""

from contextlib import asynccontextmanager

import torch
from fastapi import FastAPI, HTTPException
from peft import PeftModel
from pydantic import BaseModel, Field
from transformers import AutoModelForCausalLM, AutoTokenizer

from src.config import settings


# 서버 프로세스에서 모델과 토크나이저를 한 번만 보관할 전역 저장소입니다.
model_state: dict[str, object] = {}


class GenerateRequest(BaseModel):
    """클라이언트가 전송하는 텍스트 생성 요청 형식입니다."""

    prompt: str = Field(min_length=1, description="모델에 전달할 질문 또는 지시문")
    max_new_tokens: int = Field(default=256, ge=1, le=1024)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)


class GenerateResponse(BaseModel):
    """서버가 반환하는 생성 결과 형식입니다."""

    answer: str
    base_model: str
    adapter_path: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    """서버 시작 시 모델을 로드하고 종료 시 GPU 메모리를 정리합니다."""

    tokenizer = AutoTokenizer.from_pretrained(
        settings.base_model,
        token=settings.hf_token,
        trust_remote_code=True,
    )
    base_model = AutoModelForCausalLM.from_pretrained(
        settings.base_model,
        token=settings.hf_token,
        trust_remote_code=True,
        device_map="auto" if torch.cuda.is_available() else None,
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
    )
    model = PeftModel.from_pretrained(base_model, str(settings.adapter_path))
    model.eval()

    model_state["tokenizer"] = tokenizer
    model_state["model"] = model
    yield

    model_state.clear()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


app = FastAPI(
    title="DPO Fine-tuned Model API",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
def health() -> dict[str, object]:
    """서버와 모델 로딩 상태를 확인합니다."""

    return {
        "status": "ok",
        "model_loaded": "model" in model_state,
        "cuda_available": torch.cuda.is_available(),
    }


@app.post("/generate", response_model=GenerateResponse)
def generate(request: GenerateRequest) -> GenerateResponse:
    """DPO Adapter가 적용된 모델로 답변을 생성합니다."""

    model = model_state.get("model")
    tokenizer = model_state.get("tokenizer")
    if model is None or tokenizer is None:
        raise HTTPException(status_code=503, detail="모델이 아직 로드되지 않았습니다.")

    messages = [{"role": "user", "content": request.prompt}]
    formatted_prompt = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )
    inputs = tokenizer(formatted_prompt, return_tensors="pt").to(next(model.parameters()).device)

    with torch.no_grad():
        output_ids = model.generate(
            **inputs,
            max_new_tokens=request.max_new_tokens,
            do_sample=request.temperature > 0,
            temperature=max(request.temperature, 1e-5),
            top_p=0.9,
            pad_token_id=tokenizer.eos_token_id,
        )

    generated_ids = output_ids[0, inputs["input_ids"].shape[1]:]
    answer = tokenizer.decode(generated_ids, skip_special_tokens=True).strip()
    return GenerateResponse(
        answer=answer,
        base_model=settings.base_model,
        adapter_path=str(settings.adapter_path),
    )
