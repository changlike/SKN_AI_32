"""
저장된 모델 예측에서 품질 지표와 서비스 성능 지표를 계산합니다.
"""

# 명령행 인자를 처리하기 위해 argparse를 가져옵니다.
import argparse

# JSON 형식 준수 여부를 검사하기 위해 json을 가져옵니다.
import json

# 통계 평균과 중앙값을 계산하기 위해 statistics를 가져옵니다.
import statistics

# 모듈 검색 경로를 추가하기 위해 sys를 가져옵니다.
import sys

# 파일 경로를 처리하기 위해 Path를 가져옵니다.
from pathlib import Path

# ROUGE 점수 계산기를 가져옵니다.
from rouge_score import rouge_scorer


# 프로젝트 루트 경로를 계산합니다.
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# 프로젝트 루트를 모듈 검색 경로에 추가합니다.
sys.path.insert(0, str(PROJECT_ROOT))

# 공통 JSONL과 JSON 저장 함수를 가져옵니다.
from evaluation.common import load_jsonl, save_json


def parse_args() -> argparse.Namespace:
    """
    예측 파일과 평가 결과 저장 경로를 읽습니다.
    """

    # 명령행 파서를 생성합니다.
    parser = argparse.ArgumentParser(
        description="LLM 자동 평가 지표 계산"
    )

    # 평가할 예측 JSONL 파일을 받습니다.
    parser.add_argument(
        "--prediction-file",
        type=Path,
        required=True,
    )

    # 계산 결과를 저장할 JSON 파일을 받습니다.
    parser.add_argument(
        "--output-file",
        type=Path,
        required=True,
    )

    # 파싱된 인자를 반환합니다.
    return parser.parse_args()


def normalize_text(text: str) -> str:
    """
    Exact Match를 위해 공백과 대소문자를 정규화합니다.
    """

    # 앞뒤 공백을 제거하고 연속 공백을 하나로 합친 뒤 소문자로 변환합니다.
    return " ".join(text.strip().lower().split())


def valid_json(text: str) -> bool:
    """
    문자열이 올바른 JSON인지 검사합니다.
    """

    try:
        # 문자열을 JSON으로 파싱합니다.
        json.loads(text)

        # 파싱에 성공하면 True를 반환합니다.
        return True
    except json.JSONDecodeError:
        # JSON 문법 오류가 발생하면 False를 반환합니다.
        return False


def percentile(values: list[float], percent: float) -> float:
    """
    선형 보간 없이 가까운 순위 방식으로 백분위 값을 계산합니다.
    """

    # 값 목록을 오름차순 정렬합니다.
    sorted_values = sorted(values)

    # 백분위 위치를 0 기반 인덱스로 계산합니다.
    index = max(
        0,
        min(
            len(sorted_values) - 1,
            int(round((len(sorted_values) - 1) * percent)),
        ),
    )

    # 계산한 위치의 값을 반환합니다.
    return sorted_values[index]


def main() -> None:
    """
    Exact Match, ROUGE, JSON 준수율, latency와 처리량을 계산합니다.
    """

    # 명령행 인자를 읽습니다.
    args = parse_args()

    # 예측 데이터를 읽습니다.
    rows = load_jsonl(args.prediction_file)

    # 예측 데이터가 없으면 평가할 수 없으므로 오류를 발생시킵니다.
    if not rows:
        raise ValueError("예측 파일이 비어 있습니다.")

    # ROUGE-1, ROUGE-2, ROUGE-L 계산기를 생성합니다.
    scorer = rouge_scorer.RougeScorer(
        ["rouge1", "rouge2", "rougeL"],
        use_stemmer=False,
    )

    # 개별 평가 결과 목록을 생성합니다.
    details = []

    # JSON 출력 요구 데이터 수를 초기화합니다.
    json_target_count = 0

    # 올바른 JSON 출력 수를 초기화합니다.
    json_valid_count = 0

    # 한국어 문자가 포함된 답변 수를 초기화합니다.
    korean_answer_count = 0

    # 모든 예측 행을 반복합니다.
    for row in rows:
        # 기준 답변을 문자열로 가져옵니다.
        reference = str(row["reference"])

        # 모델 예측 답변을 문자열로 가져옵니다.
        prediction = str(row["prediction"])

        # 기준 답변과 예측 답변 사이의 ROUGE 점수를 계산합니다.
        rouge = scorer.score(reference, prediction)

        # 정규화 후 완전히 일치하는지 계산합니다.
        exact_match = int(
            normalize_text(reference) == normalize_text(prediction)
        )

        # 평가 데이터가 JSON 출력을 요구하는지 확인합니다.
        require_json = bool(row.get("require_json", False))

        # JSON 요구 데이터 수를 증가시킵니다.
        if require_json:
            json_target_count += 1

            # 모델 답변이 유효한 JSON이면 성공 수를 증가시킵니다.
            if valid_json(prediction):
                json_valid_count += 1

        # 답변에 한글 음절이 하나 이상 포함되는지 검사합니다.
        contains_korean = any(
            "가" <= character <= "힣"
            for character in prediction
        )

        # 한글 포함 답변이면 수를 증가시킵니다.
        if contains_korean:
            korean_answer_count += 1

        # 개별 상세 결과를 저장합니다.
        details.append(
            {
                "id": row["id"],
                "category": row["category"],
                "exact_match": exact_match,
                "rouge1_f1": rouge["rouge1"].fmeasure,
                "rouge2_f1": rouge["rouge2"].fmeasure,
                "rougeL_f1": rouge["rougeL"].fmeasure,
                "valid_json": (
                    valid_json(prediction)
                    if require_json
                    else None
                ),
                "contains_korean": contains_korean,
                "latency_seconds": float(row["latency_seconds"]),
                "tokens_per_second": float(
                    row.get("tokens_per_second") or 0.0
                ),
            }
        )

    # 전체 응답 시간 목록을 만듭니다.
    latency_values = [
        float(row["latency_seconds"])
        for row in rows
    ]

    # 전체 처리량 목록을 만듭니다.
    throughput_values = [
        float(row.get("tokens_per_second") or 0.0)
        for row in rows
    ]

    # 전체 평가 요약을 계산합니다.
    summary = {
        "sample_count": len(rows),
        "exact_match": statistics.mean(
            item["exact_match"] for item in details
        ),
        "rouge1_f1": statistics.mean(
            item["rouge1_f1"] for item in details
        ),
        "rouge2_f1": statistics.mean(
            item["rouge2_f1"] for item in details
        ),
        "rougeL_f1": statistics.mean(
            item["rougeL_f1"] for item in details
        ),
        "json_target_count": json_target_count,
        "json_compliance_rate": (
            json_valid_count / json_target_count
            if json_target_count
            else None
        ),
        "korean_answer_rate": korean_answer_count / len(rows),
        "average_latency_seconds": statistics.mean(latency_values),
        "median_latency_seconds": statistics.median(latency_values),
        "p95_latency_seconds": percentile(latency_values, 0.95),
        "average_tokens_per_second": statistics.mean(
            throughput_values
        ),
    }

    # 요약과 상세 결과를 하나의 객체로 구성합니다.
    result = {
        "prediction_file": str(args.prediction_file),
        "summary": summary,
        "details": details,
    }

    # 결과를 JSON 파일로 저장합니다.
    save_json(result, args.output_file)

    # 핵심 요약을 터미널에 출력합니다.
    print(json.dumps(summary, ensure_ascii=False, indent=2))


# 직접 실행한 경우에만 평가를 수행합니다.
if __name__ == "__main__":
    main()
