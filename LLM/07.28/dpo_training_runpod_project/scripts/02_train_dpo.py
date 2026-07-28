"""Hugging Face TRL, PEFT, QLoRA를 이용해 DPO 학습을 수행합니다."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

# 스크립트를 프로젝트 루트에서 직접 실행해도 src 패키지를 찾도록 루트 경로를 추가합니다.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import torch
from peft import LoraConfig
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from trl import DPOConfig, DPOTrainer

from src.config import settings
from src.data_utils import load_and_split_dataset


def parse_args() -> argparse.Namespace:
    """학습 하이퍼파라미터를 명령행에서 받을 수 있도록 정의합니다."""

    parser = argparse.ArgumentParser(description="QLoRA 기반 DPO 학습")
    parser.add_argument("--data", type=Path, default=Path("data/processed/preferences_clean.jsonl"))
    parser.add_argument("--model", type=str, default=settings.base_model)
    parser.add_argument("--output", type=Path, default=settings.adapter_path)
    parser.add_argument("--epochs", type=float, default=1.0)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--gradient-accumulation", type=int, default=8)
    parser.add_argument("--learning-rate", type=float, default=5e-5)
    parser.add_argument("--max-length", type=int, default=1024)
    parser.add_argument("--max-prompt-length", type=int, default=512)
    parser.add_argument("--beta", type=float, default=0.1)
    parser.add_argument("--no-4bit", action="store_true", help="4비트 QLoRA를 사용하지 않습니다.")
    return parser.parse_args()


def build_quantization_config(use_4bit: bool) -> BitsAndBytesConfig | None:
    """GPU 환경에서 사용할 4비트 양자화 설정을 생성합니다."""

    if not use_4bit:
        return None

    if not torch.cuda.is_available():
        raise RuntimeError("4비트 QLoRA 학습은 CUDA GPU가 필요합니다. --no-4bit 옵션을 사용하세요.")

    # NF4는 정규분포 형태의 LLM 가중치 양자화에 널리 사용하는 4비트 형식입니다.
    return BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16,
    )


def main() -> None:
    """모델, 토크나이저, 데이터셋, LoRA와 DPO 설정을 조합하여 학습합니다."""

    args = parse_args()
    use_4bit = not args.no_4bit

    # 로컬 JSONL을 Hugging Face Dataset으로 읽고 train/test로 분리합니다.
    dataset = load_and_split_dataset(args.data, test_size=0.2, seed=42)

    # 토크나이저는 문장을 모델이 처리할 토큰 ID로 변환합니다.
    tokenizer = AutoTokenizer.from_pretrained(
        args.model,
        token=settings.hf_token,
        trust_remote_code=True,
    )

    # 패딩 토큰이 없는 모델은 문장 종료 토큰을 패딩 토큰으로 재사용합니다.
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    quantization_config = build_quantization_config(use_4bit)

    # 기준 모델을 불러옵니다. device_map="auto"는 GPU 메모리에 맞춰 자동 배치합니다.
    model = AutoModelForCausalLM.from_pretrained(
        args.model,
        token=settings.hf_token,
        trust_remote_code=True,
        quantization_config=quantization_config,
        device_map="auto" if torch.cuda.is_available() else None,
        torch_dtype=(
            torch.bfloat16
            if torch.cuda.is_available() and torch.cuda.is_bf16_supported()
            else torch.float16
            if torch.cuda.is_available()
            else torch.float32
        ),
    )

    # KV cache는 추론 속도를 높이지만 학습 중 gradient checkpointing과 충돌할 수 있어 끕니다.
    model.config.use_cache = False

    # Qwen 계열의 주요 선형 투영층에 LoRA Adapter를 삽입합니다.
    peft_config = LoraConfig(
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=[
            "q_proj",
            "k_proj",
            "v_proj",
            "o_proj",
            "gate_proj",
            "up_proj",
            "down_proj",
        ],
    )

    # DPOConfig는 일반 Trainer 설정과 DPO 전용 beta, 최대 길이를 함께 관리합니다.
    training_args = DPOConfig(
        output_dir=str(args.output),
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        gradient_accumulation_steps=args.gradient_accumulation,
        learning_rate=args.learning_rate,
        beta=args.beta,
        max_length=args.max_length,
        max_prompt_length=args.max_prompt_length,
        gradient_checkpointing=True,
        logging_steps=1,
        eval_strategy="epoch",
        save_strategy="epoch",
        save_total_limit=2,
        report_to="none",
        remove_unused_columns=False,
        bf16=torch.cuda.is_available() and torch.cuda.is_bf16_supported(),
        fp16=torch.cuda.is_available() and not torch.cuda.is_bf16_supported(),
        seed=42,
    )

    # DPOTrainer는 chosen 응답의 상대 로그확률은 높이고 rejected 응답은 낮추도록 학습합니다.
    trainer = DPOTrainer(
        model=model,
        args=training_args,
        train_dataset=dataset["train"],
        eval_dataset=dataset["test"],
        processing_class=tokenizer,
        peft_config=peft_config,
    )

    # 실제 역전파와 파라미터 업데이트를 수행합니다.
    trainer.train()

    # LoRA Adapter와 토크나이저를 저장합니다.
    trainer.save_model(str(args.output))
    tokenizer.save_pretrained(str(args.output))
    print(f"[학습 완료] Adapter 저장 위치: {args.output}")


if __name__ == "__main__":
    main()
