"""
Base 모델과 DPO 모델의 저장된 평가 지표를 비교합니다.
"""

# JSON 파일을 읽고 결과를 출력하기 위해 json을 가져옵니다.
import json

# 파일 경로를 처리하기 위해 Path를 가져옵니다.
from pathlib import Path


# 프로젝트 루트 경로를 계산합니다.
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Base 모델 평가 결과 경로를 지정합니다.
BASE_METRICS_FILE = PROJECT_ROOT / "outputs/base_metrics.json"

# DPO 모델 평가 결과 경로를 지정합니다.
DPO_METRICS_FILE = PROJECT_ROOT / "outputs/dpo_metrics.json"

# 비교 결과 저장 경로를 지정합니다.
COMPARISON_FILE = PROJECT_ROOT / "outputs/comparison.json"


def load_json(file_path: Path) -> dict:
    """
    UTF-8 JSON 파일을 딕셔너리로 읽습니다.
    """

    # 파일 존재 여부를 확인합니다.
    if not file_path.exists():
        raise FileNotFoundError(f"파일이 없습니다: {file_path}")

    # UTF-8 인코딩으로 파일을 엽니다.
    with file_path.open("r", encoding="utf-8") as file:
        # JSON 내용을 파이썬 딕셔너리로 반환합니다.
        return json.load(file)


def main() -> None:
    """
    품질·형식·속도 지표의 DPO 모델 변화량을 계산합니다.
    """

    # Base 모델의 summary 지표를 읽습니다.
    base = load_json(BASE_METRICS_FILE)["summary"]

    # DPO 모델의 summary 지표를 읽습니다.
    dpo = load_json(DPO_METRICS_FILE)["summary"]

    # 비교할 지표 이름을 정의합니다.
    metric_names = [
        "exact_match",
        "rouge1_f1",
        "rouge2_f1",
        "rougeL_f1",
        "json_compliance_rate",
        "korean_answer_rate",
        "average_latency_seconds",
        "p95_latency_seconds",
        "average_tokens_per_second",
    ]

    # 지표별 비교 결과를 저장할 딕셔너리입니다.
    comparison = {}

    # 비교할 지표를 하나씩 반복합니다.
    for metric_name in metric_names:
        # Base 값을 읽습니다.
        base_value = base.get(metric_name)

        # DPO 값을 읽습니다.
        dpo_value = dpo.get(metric_name)

        # 값이 없는 지표는 변화량을 계산하지 않습니다.
        if base_value is None or dpo_value is None:
            improvement = None
        elif "latency" in metric_name:
            # 지연 시간은 감소해야 개선이므로 Base에서 DPO를 뺍니다.
            improvement = float(base_value) - float(dpo_value)
        else:
            # 품질과 처리량은 DPO에서 Base를 빼 양수면 개선입니다.
            improvement = float(dpo_value) - float(base_value)

        # 현재 지표의 비교값을 저장합니다.
        comparison[metric_name] = {
            "base": base_value,
            "dpo": dpo_value,
            "improvement_delta": improvement,
        }

    # 최종 비교 결과를 구성합니다.
    result = {
        "base": base,
        "dpo": dpo,
        "comparison": comparison,
        "interpretation": (
            "품질 지표는 양수 변화가 개선이며, "
            "latency 지표도 improvement_delta가 양수이면 DPO 쪽이 더 빠릅니다."
        ),
    }

    # 출력 디렉터리를 생성합니다.
    COMPARISON_FILE.parent.mkdir(parents=True, exist_ok=True)

    # 비교 결과를 UTF-8 JSON으로 저장합니다.
    with COMPARISON_FILE.open("w", encoding="utf-8") as file:
        json.dump(result, file, ensure_ascii=False, indent=2)

    # 비교 결과를 화면에 출력합니다.
    print(json.dumps(result, ensure_ascii=False, indent=2))


# 직접 실행한 경우에만 비교를 수행합니다.
if __name__ == "__main__":
    main()
