"""
Qwen Instruct 모델에 QLoRA와 DPO를 적용하여 한국어 선호 학습을 수행합니다.
"""

# 명령행 학습 옵션을 처리하기 위해 argparse를 가져옵니다.
import argparse

# 환경변수의 Hugging Face 토큰을 읽기 위해 os를 가져옵니다.
import os

# 데이터 파일 경로와 출력 경로를 처리하기 위해 Path를 가져옵니다.
from pathlib import Path

# .env 파일을 자동으로 읽기 위해 load_dotenv를 가져옵니다.
from dotenv import load_dotenv


# 프로젝트 루트의 .env 파일을 읽어 환경변수에 반영합니다.
load_dotenv(Path(__file__).resolve().parents[1] / ".env")


def parse_args() -> argparse.Namespace:
    """
    DPO 학습에 필요한 모델, 데이터, 하이퍼파라미터를 읽습니다.
    """

    # 명령행 파서를 생성합니다.
    parser = argparse.ArgumentParser(
        description="한국어 QLoRA DPO 학습"
    )

    # 학습 기준이 되는 Hugging Face 모델 이름을 받습니다.
    parser.add_argument(
        "--base-model",
        default=os.getenv(
            "BASE_MODEL_NAME",
            "Qwen/Qwen2.5-1.5B-Instruct",
        ),
    )

    # 학습 JSONL 파일 경로를 받습니다.
    parser.add_argument(
        "--train-file",
        type=Path,
        default=Path("data/dpo_train.jsonl"),
    )

    # 검증 JSONL 파일 경로를 받습니다.
    parser.add_argument(
        "--eval-file",
        type=Path,
        default=Path("data/dpo_eval.jsonl"),
    )

    # 학습 Adapter 저장 경로를 받습니다.
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("models/dpo_adapter"),
    )

    # 전체 학습 반복 횟수를 받습니다.
    parser.add_argument("--epochs", type=float, default=1.0)

    # GPU 한 장당 미니배치 크기를 받습니다.
    parser.add_argument("--batch-size", type=int, default=1)

    # 그래디언트 누적 횟수를 받습니다.
    parser.add_argument(
        "--gradient-accumulation-steps",
        type=int,
        default=8,
    )

    # 옵티마이저 학습률을 받습니다.
    parser.add_argument(
        "--learning-rate",
        type=float,
        default=5e-6,
    )

    # DPO 기준 모델 대비 편차를 조절하는 beta를 받습니다.
    parser.add_argument("--beta", type=float, default=0.1)

    # prompt와 completion을 합친 최대 토큰 길이를 받습니다.
    parser.add_argument("--max-length", type=int, default=1024)

    # LoRA 저차원 행렬의 rank 값을 받습니다.
    parser.add_argument("--lora-r", type=int, default=16)

    # LoRA 스케일 조절값을 받습니다.
    parser.add_argument("--lora-alpha", type=int, default=32)

    # LoRA 층에 사용할 dropout 값을 받습니다.
    parser.add_argument("--lora-dropout", type=float, default=0.05)

    # 재현 가능한 학습을 위한 난수 시드를 받습니다.
    parser.add_argument("--seed", type=int, default=42)

    # 완성된 인자를 반환합니다.
    return parser.parse_args()


def main() -> None:
    """
    4비트 기반 모델에 LoRA Adapter를 추가하고 DPOTrainer로 학습합니다.
    """

    # 명령행 학습 옵션을 읽습니다.
    args = parse_args()

    # 학습 파일이 존재하는지 확인합니다.
    if not args.train_file.exists():
        raise FileNotFoundError(
            f"학습 파일이 없습니다: {args.train_file}"
        )

    # 검증 파일이 존재하는지 확인합니다.
    if not args.eval_file.exists():
        raise FileNotFoundError(
            f"검증 파일이 없습니다: {args.eval_file}"
        )

    # 실제 텐서 연산에 필요한 PyTorch를 가져옵니다.
    import torch

    # JSONL 데이터를 Hugging Face Dataset으로 읽기 위해 load_dataset을 가져옵니다.
    from datasets import load_dataset

    # QLoRA 설정 클래스를 가져옵니다.
    from peft import LoraConfig

    # DPO 전용 학습 설정과 Trainer를 가져옵니다.
    from trl import DPOConfig, DPOTrainer

    # 4비트 양자화 설정과 모델·토크나이저 클래스를 가져옵니다.
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        BitsAndBytesConfig,
        set_seed,
    )

    # CUDA GPU가 없으면 QLoRA 실습을 중단합니다.
    if not torch.cuda.is_available():
        raise RuntimeError(
            "CUDA GPU를 사용할 수 없습니다. RunPod GPU Pod에서 실행하세요."
        )

    # 동일한 학습 결과 재현 가능성을 높이기 위해 난수 시드를 고정합니다.
    set_seed(args.seed)

    # GPU가 BF16을 지원하는지 확인합니다.
    bf16_supported = torch.cuda.is_bf16_supported()

    # BF16 지원 시 bfloat16, 아니면 float16을 계산 자료형으로 선택합니다.
    compute_dtype = (
        torch.bfloat16
        if bf16_supported
        else torch.float16
    )

    # NF4 방식의 QLoRA 4비트 양자화 설정을 생성합니다.
    quantization_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=compute_dtype,
    )

    # Hugging Face 토큰이 설정된 경우에만 공통 인자에 추가합니다.
    common_kwargs = {}
    hf_token = os.getenv("HF_TOKEN")
    if hf_token:
        common_kwargs["token"] = hf_token

    # 모델과 같은 저장소의 토크나이저를 불러옵니다.
    tokenizer = AutoTokenizer.from_pretrained(
        args.base_model,
        trust_remote_code=True,
        **common_kwargs,
    )

    # 패딩 토큰이 없으면 종료 토큰을 패딩 토큰으로 사용합니다.
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # Causal LLM 기반 모델을 4비트로 GPU에 적재합니다.
    model = AutoModelForCausalLM.from_pretrained(
        args.base_model,
        quantization_config=quantization_config,
        device_map="auto",
        torch_dtype=compute_dtype,
        trust_remote_code=True,
        **common_kwargs,
    )

    # 학습 시 캐시를 끄지 않으면 gradient checkpointing과 충돌할 수 있습니다.
    model.config.use_cache = False

    # JSONL 학습·검증 파일을 Dataset으로 읽습니다.
    datasets = load_dataset(
        "json",
        data_files={
            "train": str(args.train_file),
            "validation": str(args.eval_file),
        },
    )

    # Qwen 계열의 주요 선형층에 LoRA를 적용하도록 설정합니다.
    peft_config = LoraConfig(
        r=args.lora_r,
        lora_alpha=args.lora_alpha,
        lora_dropout=args.lora_dropout,
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

    # 학습 로그와 체크포인트 저장 디렉터리를 생성합니다.
    args.output_dir.mkdir(parents=True, exist_ok=True)

    # TRL DPOTrainer가 사용할 전체 학습 설정을 생성합니다.
    training_args = DPOConfig(
        output_dir=str(args.output_dir),
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=1,
        gradient_accumulation_steps=args.gradient_accumulation_steps,
        learning_rate=args.learning_rate,
        beta=args.beta,
        max_length=args.max_length,
        logging_steps=1,
        eval_strategy="steps",
        eval_steps=5,
        save_strategy="steps",
        save_steps=5,
        save_total_limit=2,
        warmup_ratio=0.1,
        lr_scheduler_type="cosine",
        optim="paged_adamw_8bit",
        gradient_checkpointing=True,
        bf16=bf16_supported,
        fp16=not bf16_supported,
        report_to="none",
        remove_unused_columns=False,
        seed=args.seed,
    )

    # 모델, 선호 데이터, LoRA 설정을 연결한 DPO Trainer를 생성합니다.
    trainer = DPOTrainer(
        model=model,
        args=training_args,
        train_dataset=datasets["train"],
        eval_dataset=datasets["validation"],
        processing_class=tokenizer,
        peft_config=peft_config,
    )

    # DPO 학습을 시작합니다.
    trainer.train()

    # 최종 LoRA Adapter 가중치와 설정을 저장합니다.
    trainer.save_model(str(args.output_dir))

    # 추론에 필요한 토크나이저도 같은 디렉터리에 저장합니다.
    tokenizer.save_pretrained(str(args.output_dir))

    # 최종 검증 평가를 실행합니다.
    evaluation_metrics = trainer.evaluate()

    # 평가 지표를 로그와 JSON 파일에 저장합니다.
    trainer.log_metrics("eval", evaluation_metrics)
    trainer.save_metrics("eval", evaluation_metrics)

    # 저장 경로를 출력합니다.
    print(f"DPO Adapter 저장 완료: {args.output_dir}")


# 직접 실행한 경우에만 학습을 시작합니다.
if __name__ == "__main__":
    main()
