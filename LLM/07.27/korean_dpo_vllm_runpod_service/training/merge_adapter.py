"""
DPO LoRA Adapter를 Base 모델에 병합하여 vLLM용 독립 모델을 생성합니다.
"""

# 명령행 인자를 처리하기 위해 argparse를 가져옵니다.
import argparse

# 환경변수에서 기본 모델 경로를 읽기 위해 os를 가져옵니다.
import os

# 파일 경로를 처리하기 위해 Path를 가져옵니다.
from pathlib import Path

# .env 파일을 읽기 위해 load_dotenv를 가져옵니다.
from dotenv import load_dotenv


# 프로젝트 루트의 .env 파일을 읽습니다.
load_dotenv(Path(__file__).resolve().parents[1] / ".env")


def parse_args() -> argparse.Namespace:
    """
    병합에 필요한 Base 모델, Adapter, 출력 경로를 읽습니다.
    """

    # 명령행 파서를 생성합니다.
    parser = argparse.ArgumentParser(description="DPO Adapter 병합")

    # 기반 모델 이름 또는 경로를 받습니다.
    parser.add_argument(
        "--base-model",
        default=os.getenv(
            "BASE_MODEL_NAME",
            "Qwen/Qwen2.5-1.5B-Instruct",
        ),
    )

    # 학습된 LoRA Adapter 경로를 받습니다.
    parser.add_argument(
        "--adapter-path",
        type=Path,
        default=Path("models/dpo_adapter"),
    )

    # 병합 모델 출력 경로를 받습니다.
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("models/merged_model"),
    )

    # 병합 시 사용할 16비트 자료형을 선택합니다.
    parser.add_argument(
        "--dtype",
        choices=["float16", "bfloat16"],
        default="bfloat16",
    )

    # 파싱한 인자를 반환합니다.
    return parser.parse_args()


def main() -> None:
    """
    16비트 Base 모델에 Adapter를 결합한 뒤 독립 모델로 저장합니다.
    """

    # 명령행 인자를 읽습니다.
    args = parse_args()

    # Adapter 디렉터리가 존재하는지 확인합니다.
    if not args.adapter_path.exists():
        raise FileNotFoundError(
            f"Adapter 경로가 없습니다: {args.adapter_path}"
        )

    # PyTorch 자료형과 모델 처리를 위해 torch를 가져옵니다.
    import torch

    # Base 모델에 PEFT Adapter를 연결하기 위해 PeftModel을 가져옵니다.
    from peft import PeftModel

    # 모델과 토크나이저 로딩 클래스를 가져옵니다.
    from transformers import AutoModelForCausalLM, AutoTokenizer

    # 사용자가 선택한 문자열을 실제 PyTorch dtype으로 변환합니다.
    dtype = (
        torch.float16
        if args.dtype == "float16"
        else torch.bfloat16
    )

    # 비공개 모델 접근 토큰이 있을 때만 전달합니다.
    common_kwargs = {}
    hf_token = os.getenv("HF_TOKEN")
    if hf_token:
        common_kwargs["token"] = hf_token

    # 4비트가 아닌 16비트 Base 모델을 CPU에 불러옵니다.
    base_model = AutoModelForCausalLM.from_pretrained(
        args.base_model,
        torch_dtype=dtype,
        device_map="cpu",
        low_cpu_mem_usage=True,
        trust_remote_code=True,
        **common_kwargs,
    )

    # Base 모델에 DPO로 학습한 LoRA Adapter를 연결합니다.
    peft_model = PeftModel.from_pretrained(
        base_model,
        str(args.adapter_path),
    )

    # LoRA 가중치를 Base 가중치에 병합하고 PEFT 래퍼를 제거합니다.
    merged_model = peft_model.merge_and_unload()

    # 출력 디렉터리를 생성합니다.
    args.output_dir.mkdir(parents=True, exist_ok=True)

    # 병합 모델을 안전한 safetensors 형식으로 저장합니다.
    merged_model.save_pretrained(
        str(args.output_dir),
        safe_serialization=True,
        max_shard_size="4GB",
    )

    # 기반 모델 토크나이저를 불러옵니다.
    tokenizer = AutoTokenizer.from_pretrained(
        args.base_model,
        trust_remote_code=True,
        **common_kwargs,
    )

    # 토크나이저를 병합 모델 디렉터리에 저장합니다.
    tokenizer.save_pretrained(str(args.output_dir))

    # 저장 경로를 출력합니다.
    print(f"병합 모델 저장 완료: {args.output_dir}")


# 직접 실행한 경우에만 병합을 수행합니다.
if __name__ == "__main__":
    main()
