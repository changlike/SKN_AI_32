"""
평가 데이터 로드, vLLM 호출, JSONL 저장에 공통으로 사용하는 함수입니다.
"""

# JSON과 JSONL 파일 처리를 위해 json을 가져옵니다.
import json

# 응답 시간을 측정하기 위해 time을 가져옵니다.
import time

# 파일 경로를 처리하기 위해 Path를 가져옵니다.
from pathlib import Path

# 다양한 값의 딕셔너리를 표현하기 위해 Any를 가져옵니다.
from typing import Any

# OpenAI 호환 vLLM 서버를 호출하기 위해 OpenAI를 가져옵니다.
from openai import OpenAI


def load_jsonl(file_path: Path) -> list[dict[str, Any]]:
    """
    UTF-8 JSONL 파일을 딕셔너리 목록으로 읽습니다.
    """

    # 파일 존재 여부를 확인합니다.
    if not file_path.exists():
        raise FileNotFoundError(f"파일이 없습니다: {file_path}")

    # 읽은 데이터를 저장할 목록입니다.
    rows: list[dict[str, Any]] = []

    # UTF-8 인코딩으로 파일을 엽니다.
    with file_path.open("r", encoding="utf-8") as file:
        # 한 줄씩 반복합니다.
        for line_number, line in enumerate(file, start=1):
            # 빈 줄은 건너뜁니다.
            if not line.strip():
                continue

            try:
                # JSON 문자열을 파이썬 딕셔너리로 변환합니다.
                rows.append(json.loads(line))
            except json.JSONDecodeError as error:
                # 오류가 발생한 줄 번호를 포함해 예외를 발생시킵니다.
                raise ValueError(
                    f"{file_path}의 {line_number}번째 줄 JSON이 잘못되었습니다."
                ) from error

    # 데이터 목록을 반환합니다.
    return rows


def save_jsonl(rows: list[dict[str, Any]], file_path: Path) -> None:
    """
    딕셔너리 목록을 UTF-8 JSONL 파일로 저장합니다.
    """

    # 상위 디렉터리가 없으면 생성합니다.
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # UTF-8 쓰기 모드로 파일을 엽니다.
    with file_path.open("w", encoding="utf-8") as file:
        # 데이터를 한 건씩 반복합니다.
        for row in rows:
            # 한글을 유지한 JSON 문자열을 한 줄로 저장합니다.
            file.write(json.dumps(row, ensure_ascii=False) + "\n")


def save_json(data: dict[str, Any], file_path: Path) -> None:
    """
    딕셔너리를 들여쓰기된 UTF-8 JSON 파일로 저장합니다.
    """

    # 상위 디렉터리를 생성합니다.
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # UTF-8 쓰기 모드로 파일을 엽니다.
    with file_path.open("w", encoding="utf-8") as file:
        # 한글 유지와 두 칸 들여쓰기를 적용해 저장합니다.
        json.dump(data, file, ensure_ascii=False, indent=2)


def generate_one(
    client: OpenAI,
    model_name: str,
    prompt: str,
    system_prompt: str,
    max_tokens: int,
) -> dict[str, Any]:
    """
    vLLM에 한 질문을 보내고 답변 및 성능 정보를 반환합니다.
    """

    # 추론 요청 시작 시각을 기록합니다.
    started_at = time.perf_counter()

    # OpenAI 호환 Chat Completions API를 호출합니다.
    completion = client.chat.completions.create(
        model=model_name,
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.0,
        max_tokens=max_tokens,
    )

    # 전체 요청 시간을 계산합니다.
    latency = max(time.perf_counter() - started_at, 0.000001)

    # 첫 번째 답변 문자열을 읽습니다.
    answer = completion.choices[0].message.content or ""

    # 토큰 사용량 객체를 읽습니다.
    usage = completion.usage

    # 출력 토큰 수를 안전하게 읽습니다.
    output_tokens = usage.completion_tokens if usage else 0

    # 모델 답변과 성능 정보를 반환합니다.
    return {
        "prediction": answer.strip(),
        "latency_seconds": latency,
        "prompt_tokens": usage.prompt_tokens if usage else None,
        "output_tokens": output_tokens,
        "total_tokens": usage.total_tokens if usage else None,
        "tokens_per_second": (
            output_tokens / latency
            if output_tokens is not None
            else None
        ),
    }
