"""기준 모델과 DPO Adapter 모델의 선호도 정확도를 비교합니다."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

# 스크립트를 프로젝트 루트에서 직접 실행해도 src 패키지를 찾도록 루트 경로를 추가합니다.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import torch
from datasets import load_dataset
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

from src.config import settings


def sequence_log_probability(model, tokenizer, prompt: str, answer: str) -> float:
    """prompt 다음에 answer가 생성될 조건부 로그확률의 합을 계산합니다."""

    prompt_ids = tokenizer(prompt, return_tensors="pt", add_special_tokens=False).input_ids
    full_ids = tokenizer(prompt + answer, return_tensors="pt", add_special_tokens=False).input_ids
    device = next(model.parameters()).device
    prompt_ids = prompt_ids.to(device)
    full_ids = full_ids.to(device)

    with torch.no_grad():
        logits = model(full_ids).logits[:, :-1, :]

    labels = full_ids[:, 1:]
    log_probs = torch.log_softmax(logits, dim=-1)
    token_log_probs = log_probs.gather(dim=-1, index=labels.unsqueeze(-1)).squeeze(-1)

    # prompt 구간을 제외하고 answer 토큰에 해당하는 로그확률만 합산합니다.
    answer_start = max(prompt_ids.shape[1] - 1, 0)
    return token_log_probs[:, answer_start:].sum().item()


def preference_accuracy(model, tokenizer, dataset) -> float:
    """chosen 로그확률이 rejected보다 높은 데이터 비율을 계산합니다."""

    correct = 0
    for row in dataset:
        chosen_score = sequence_log_probability(model, tokenizer, row["prompt"], row["chosen"])
        rejected_score = sequence_log_probability(model, tokenizer, row["prompt"], row["rejected"])
        correct += int(chosen_score > rejected_score)
    return correct / len(dataset)


def main() -> None:
    """기준 모델과 Adapter 적용 모델을 같은 데이터로 평가합니다."""

    parser = argparse.ArgumentParser(description="DPO 선호도 정확도 평가")
    parser.add_argument("--data", type=Path, default=Path("data/processed/preferences_clean.jsonl"))
    parser.add_argument("--model", type=str, default=settings.base_model)
    parser.add_argument("--adapter", type=Path, default=settings.adapter_path)
    args = parser.parse_args()

    tokenizer = AutoTokenizer.from_pretrained(args.model, token=settings.hf_token, trust_remote_code=True)
    base_model = AutoModelForCausalLM.from_pretrained(
        args.model,
        token=settings.hf_token,
        trust_remote_code=True,
        device_map="auto" if torch.cuda.is_available() else None,
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
    )

    dataset = load_dataset("json", data_files=str(args.data), split="train")
    base_accuracy = preference_accuracy(base_model, tokenizer, dataset)

    # 동일한 기준 모델에 학습된 LoRA Adapter를 결합합니다.
    dpo_model = PeftModel.from_pretrained(base_model, str(args.adapter))
    dpo_accuracy = preference_accuracy(dpo_model, tokenizer, dataset)

    print(f"기준 모델 선호도 정확도: {base_accuracy:.4f}")
    print(f"DPO 모델 선호도 정확도: {dpo_accuracy:.4f}")
    print(f"정확도 변화: {dpo_accuracy - base_accuracy:+.4f}")


if __name__ == "__main__":
    main()
