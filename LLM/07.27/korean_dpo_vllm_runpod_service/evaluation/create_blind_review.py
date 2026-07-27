"""
Base와 DPO 답변을 A/B로 섞어 사람 블라인드 평가 CSV를 생성합니다.
"""

# JSONL과 정답표 처리를 위해 json을 가져옵니다.
import json

# 답변 배치를 무작위로 정하기 위해 random을 가져옵니다.
import random

# 파일 경로를 처리하기 위해 Path를 가져옵니다.
from pathlib import Path

# CSV 저장을 위해 pandas를 가져옵니다.
import pandas as pd


# 프로젝트 루트 경로를 계산합니다.
PROJECT_ROOT = Path(__file__).resolve().parents[1]


def load_jsonl(file_path: Path) -> list[dict]:
    """
    JSONL 파일을 딕셔너리 목록으로 읽습니다.
    """

    # 파일 존재 여부를 확인합니다.
    if not file_path.exists():
        raise FileNotFoundError(f"파일이 없습니다: {file_path}")

    # 결과 목록을 생성합니다.
    rows = []

    # UTF-8 인코딩으로 파일을 엽니다.
    with file_path.open("r", encoding="utf-8") as file:
        # 한 줄씩 읽습니다.
        for line in file:
            # 빈 줄은 무시합니다.
            if not line.strip():
                continue

            # JSON 문자열을 딕셔너리로 변환해 추가합니다.
            rows.append(json.loads(line))

    # 전체 결과를 반환합니다.
    return rows


def main() -> None:
    """
    모델 이름을 숨긴 평가표와 A/B 정답표를 생성합니다.
    """

    # 재현 가능한 무작위 배치를 위해 시드를 고정합니다.
    random.seed(42)

    # Base 모델 예측 결과를 읽습니다.
    base_rows = load_jsonl(
        PROJECT_ROOT / "outputs/base_predictions.jsonl"
    )

    # DPO 모델 예측 결과를 읽습니다.
    dpo_rows = load_jsonl(
        PROJECT_ROOT / "outputs/dpo_predictions.jsonl"
    )

    # ID로 Base 결과를 찾을 딕셔너리를 만듭니다.
    base_map = {str(row["id"]): row for row in base_rows}

    # ID로 DPO 결과를 찾을 딕셔너리를 만듭니다.
    dpo_map = {str(row["id"]): row for row in dpo_rows}

    # 사람이 입력할 평가 행 목록입니다.
    review_rows = []

    # 실제 A/B 모델 매핑 정답표입니다.
    answer_key = {}

    # 두 결과에 모두 있는 평가 ID만 반복합니다.
    for evaluation_id in sorted(set(base_map) & set(dpo_map)):
        # 현재 Base 모델 결과를 읽습니다.
        base_row = base_map[evaluation_id]

        # 현재 DPO 모델 결과를 읽습니다.
        dpo_row = dpo_map[evaluation_id]

        # A와 B의 모델 배치를 무작위로 결정합니다.
        if random.randint(0, 1) == 0:
            answer_a = base_row["prediction"]
            answer_b = dpo_row["prediction"]
            model_a = "base"
            model_b = "dpo"
        else:
            answer_a = dpo_row["prediction"]
            answer_b = base_row["prediction"]
            model_a = "dpo"
            model_b = "base"

        # 사람이 점수를 입력할 CSV 행을 생성합니다.
        review_rows.append(
            {
                "id": evaluation_id,
                "category": base_row["category"],
                "prompt": base_row["prompt"],
                "reference": base_row["reference"],
                "answer_a": answer_a,
                "answer_b": answer_b,
                "winner_A_B_TIE": "",
                "a_accuracy_1_5": "",
                "b_accuracy_1_5": "",
                "a_relevance_1_5": "",
                "b_relevance_1_5": "",
                "a_korean_naturalness_1_5": "",
                "b_korean_naturalness_1_5": "",
                "a_kindness_1_5": "",
                "b_kindness_1_5": "",
                "a_safety_1_5": "",
                "b_safety_1_5": "",
                "comment": "",
            }
        )

        # 숨겨진 실제 모델 정보를 정답표에 기록합니다.
        answer_key[evaluation_id] = {
            "answer_a_model": model_a,
            "answer_b_model": model_b,
        }

    # 출력 디렉터리를 생성합니다.
    output_dir = PROJECT_ROOT / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)

    # 평가 행을 DataFrame으로 변환합니다.
    dataframe = pd.DataFrame(review_rows)

    # Excel에서 한글이 깨지지 않도록 UTF-8 BOM CSV로 저장합니다.
    dataframe.to_csv(
        output_dir / "human_review.csv",
        index=False,
        encoding="utf-8-sig",
    )

    # A/B 정답표를 JSON 파일로 저장합니다.
    with (output_dir / "human_review_answer_key.json").open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(answer_key, file, ensure_ascii=False, indent=2)

    # 생성된 평가 건수를 출력합니다.
    print(f"블라인드 평가 파일 생성 완료: {len(review_rows)}건")


# 직접 실행한 경우에만 평가 파일을 생성합니다.
if __name__ == "__main__":
    main()
