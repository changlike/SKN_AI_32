"""DPO 선호도 데이터의 검증, 변환, 분할 기능을 제공합니다."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any



# DPO 데이터에 반드시 존재해야 하는 열 이름입니다.
REQUIRED_COLUMNS = {"prompt", "chosen", "rejected"}


def validate_record(record: dict[str, Any], line_number: int) -> list[str]:
    """JSONL 한 행을 검사하고 발견된 오류 메시지 목록을 반환합니다."""

    errors: list[str] = []

    # 필수 키가 누락되었는지 확인합니다.
    missing = REQUIRED_COLUMNS - set(record)
    if missing:
        errors.append(f"{line_number}행: 필수 필드 누락 {sorted(missing)}")
        return errors

    # 세 필드는 모두 비어 있지 않은 문자열이어야 합니다.
    for field in REQUIRED_COLUMNS:
        value = record[field]
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{line_number}행: '{field}'는 비어 있지 않은 문자열이어야 합니다.")

    # chosen과 rejected가 같으면 선호도 학습 신호가 만들어지지 않습니다.
    if record.get("chosen", "").strip() == record.get("rejected", "").strip():
        errors.append(f"{line_number}행: chosen과 rejected가 동일합니다.")

    return errors


def validate_jsonl(input_path: Path) -> tuple[list[dict[str, str]], list[str]]:
    """JSONL 전체를 읽어 정상 레코드와 오류 목록을 분리합니다."""

    valid_records: list[dict[str, str]] = []
    errors: list[str] = []

    # UTF-8 인코딩으로 파일을 열어 한국어가 깨지지 않도록 합니다.
    with input_path.open("r", encoding="utf-8") as file:
        for line_number, raw_line in enumerate(file, start=1):
            # 빈 줄은 데이터로 간주하지 않고 건너뜁니다.
            if not raw_line.strip():
                continue

            try:
                # 각 줄을 독립적인 JSON 객체로 변환합니다.
                record = json.loads(raw_line)
            except json.JSONDecodeError as exc:
                errors.append(f"{line_number}행: JSON 파싱 오류 - {exc}")
                continue

            # JSON 객체가 아닌 배열이나 숫자가 들어온 경우를 차단합니다.
            if not isinstance(record, dict):
                errors.append(f"{line_number}행: JSON 객체 형식이어야 합니다.")
                continue

            record_errors = validate_record(record, line_number)
            if record_errors:
                errors.extend(record_errors)
                continue

            # 앞뒤 공백을 제거해 토큰 낭비와 중복 문제를 줄입니다.
            valid_records.append(
                {
                    "prompt": record["prompt"].strip(),
                    "chosen": record["chosen"].strip(),
                    "rejected": record["rejected"].strip(),
                }
            )

    return valid_records, errors


def save_jsonl(records: list[dict[str, str]], output_path: Path) -> None:
    """검증된 레코드를 UTF-8 JSONL 파일로 저장합니다."""

    # 출력 디렉터리가 없으면 부모 디렉터리까지 생성합니다.
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as file:
        for record in records:
            # ensure_ascii=False는 한국어를 \uXXXX로 변환하지 않고 그대로 저장합니다.
            file.write(json.dumps(record, ensure_ascii=False) + "\n")


def load_and_split_dataset(
    input_path: Path,
    test_size: float = 0.2,
    seed: int = 42,
) -> "DatasetDict":
    """로컬 JSONL을 Hugging Face Dataset으로 읽고 학습/평가 세트로 분할합니다."""

    # datasets 패키지는 실제 학습 데이터 로딩 시점에만 가져옵니다.
    # 따라서 JSONL 형식 검증만 수행할 때는 무거운 ML 의존성이 없어도 됩니다.
    from datasets import Dataset, DatasetDict, load_dataset

    # Hugging Face Datasets의 json 로더는 JSON과 JSONL을 모두 처리할 수 있습니다.
    dataset: Dataset = load_dataset(
        "json",
        data_files=str(input_path),
        split="train",
    )

    # 데이터가 너무 적어 분할할 수 없는 경우 명확한 예외를 발생시킵니다.
    if len(dataset) < 2:
        raise ValueError("DPO 학습/평가 분할을 위해 최소 2개 이상의 레코드가 필요합니다.")

    # seed를 고정하면 실행할 때마다 동일한 학습/평가 분할을 재현할 수 있습니다.
    return dataset.train_test_split(test_size=test_size, seed=seed)
