"""
현재 실행 중인 vLLM 모델로 전체 평가 데이터의 예측을 생성합니다.
"""

# 명령행 인자를 처리하기 위해 argparse를 가져옵니다.
import argparse

# 환경변수의 vLLM 연결 설정을 읽기 위해 os를 가져옵니다.
import os

# 프로젝트 모듈 경로 추가를 위해 sys를 가져옵니다.
import sys

# 파일 경로를 처리하기 위해 Path를 가져옵니다.
from pathlib import Path

# .env 파일을 읽기 위해 load_dotenv를 가져옵니다.
from dotenv import load_dotenv

# OpenAI 호환 vLLM 서버 클라이언트를 가져옵니다.
from openai import OpenAI


# 프로젝트 루트 경로를 계산합니다.
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# 프로젝트 루트를 모듈 검색 경로에 추가합니다.
sys.path.insert(0, str(PROJECT_ROOT))

# 평가 공통 함수를 가져옵니다.
from evaluation.common import generate_one, load_jsonl, save_jsonl


# 프로젝트 .env 파일을 읽습니다.
load_dotenv(PROJECT_ROOT / ".env")


def parse_args() -> argparse.Namespace:
    """
    평가 입력·출력 경로와 생성 설정을 읽습니다.
    """

    # 명령행 파서를 생성합니다.
    parser = argparse.ArgumentParser(
        description="vLLM 평가 예측 생성"
    )

    # 평가 JSONL 파일 경로를 받습니다.
    parser.add_argument(
        "--input-file",
        type=Path,
        default=PROJECT_ROOT / "data/evaluation.jsonl",
    )

    # 예측 저장 JSONL 파일 경로를 받습니다.
    parser.add_argument(
        "--output-file",
        type=Path,
        required=True,
    )

    # 생성할 최대 출력 토큰 수를 받습니다.
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=512,
    )

    # 전체 데이터 중 최대 평가 개수를 받습니다.
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
    )

    # 파싱된 인자를 반환합니다.
    return parser.parse_args()


def main() -> None:
    """
    평가 질문을 순서대로 vLLM에 보내 예측 결과를 저장합니다.
    """

    # 명령행 인자를 읽습니다.
    args = parse_args()

    # vLLM 연결 주소를 환경변수에서 읽습니다.
    base_url = os.getenv(
        "VLLM_BASE_URL",
        "http://127.0.0.1:8001/v1",
    )

    # vLLM API 키를 환경변수에서 읽습니다.
    api_key = os.getenv("VLLM_API_KEY", "local-vllm-key")

    # vLLM served model 이름을 읽습니다.
    model_name = os.getenv(
        "VLLM_MODEL_NAME",
        "korean-dpo-model",
    )

    # vLLM OpenAI 호환 클라이언트를 생성합니다.
    client = OpenAI(
        base_url=base_url,
        api_key=api_key,
        timeout=120.0,
        max_retries=1,
    )

    # 평가 JSONL 데이터를 읽습니다.
    rows = load_jsonl(args.input_file)

    # limit이 있으면 앞에서부터 지정 개수만 선택합니다.
    if args.limit is not None:
        rows = rows[: args.limit]

    # 전체 예측 결과를 저장할 리스트입니다.
    predictions = []

    # 평가 데이터를 한 건씩 반복합니다.
    for index, row in enumerate(rows, start=1):
        # 현재 진행 상황을 출력합니다.
        print(f"[{index}/{len(rows)}] {row['id']} 생성 중")

        # 현재 질문을 vLLM에 전달합니다.
        generated = generate_one(
            client=client,
            model_name=model_name,
            prompt=str(row["prompt"]),
            system_prompt=(
                "당신은 정확하고 친절한 한국어 AI입니다. "
                "확인되지 않은 사실을 임의로 만들지 말고 요청 형식을 지키세요."
            ),
            max_tokens=args.max_tokens,
        )

        # 원본 평가 정보와 생성 결과를 하나의 딕셔너리로 결합합니다.
        predictions.append(
            {
                **row,
                "served_model_name": model_name,
                **generated,
            }
        )

    # 전체 결과를 JSONL 파일로 저장합니다.
    save_jsonl(predictions, args.output_file)

    # 완료 정보를 출력합니다.
    print(f"예측 저장 완료: {args.output_file}")


# 직접 실행한 경우에만 예측 생성을 수행합니다.
if __name__ == "__main__":
    main()
