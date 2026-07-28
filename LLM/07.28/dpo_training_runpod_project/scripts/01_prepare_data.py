"""원본 선호도 JSONL을 검증하고 학습용 파일로 정리하는 실행 스크립트입니다."""

import argparse
from pathlib import Path
import sys

# 스크립트를 프로젝트 루트에서 직접 실행해도 src 패키지를 찾도록 루트 경로를 추가합니다.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.data_utils import save_jsonl, validate_jsonl


def parse_args() -> argparse.Namespace:
    """명령행 인자를 정의하고 파싱합니다."""

    parser = argparse.ArgumentParser(description="DPO 선호도 데이터 검증 및 정제")
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/raw/preferences.jsonl"),
        help="검증할 원본 JSONL 경로",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/processed/preferences_clean.jsonl"),
        help="정상 레코드를 저장할 JSONL 경로",
    )
    return parser.parse_args()


def main() -> None:
    """데이터를 검증하고 오류가 없을 때 정제 파일을 저장합니다."""

    args = parse_args()
    valid_records, errors = validate_jsonl(args.input)

    # 오류를 모두 출력하여 어느 행을 고쳐야 하는지 한 번에 확인할 수 있게 합니다.
    if errors:
        print("[검증 실패]")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)

    save_jsonl(valid_records, args.output)
    print(f"[검증 성공] {len(valid_records)}개 레코드를 저장했습니다: {args.output}")


if __name__ == "__main__":
    # 이 파일을 직접 실행했을 때만 main 함수를 호출합니다.
    main()
