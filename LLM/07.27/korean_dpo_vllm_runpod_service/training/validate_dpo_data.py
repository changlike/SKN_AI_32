"""
DPO JSONL 데이터의 필수 구조와 기본 품질을 검사합니다.
"""

# 명령행 인자를 처리하기 위해 argparse를 가져옵니다.
import argparse

# JSONL 데이터를 읽기 위해 json을 가져옵니다.
import json

# 파일 경로를 안전하게 처리하기 위해 Path를 가져옵니다.
from pathlib import Path


def parse_args() -> argparse.Namespace:
    """
    검증할 JSONL 파일 경로를 명령행에서 읽습니다.
    """

    # 명령행 인자 파서를 생성합니다.
    parser = argparse.ArgumentParser(description="DPO 데이터 검증")

    # --file 인자로 검사 대상 파일을 받습니다.
    parser.add_argument("--file", type=Path, required=True)

    # 파싱된 명령행 인자를 반환합니다.
    return parser.parse_args()


def validate_messages(value: object, field_name: str, line_number: int) -> None:
    """
    prompt, chosen, rejected가 채팅 메시지 목록인지 검사합니다.
    """

    # 값이 비어 있지 않은 리스트인지 확인합니다.
    if not isinstance(value, list) or not value:
        raise ValueError(
            f"{line_number}번째 줄의 {field_name}은 비어 있지 않은 리스트여야 합니다."
        )

    # 메시지를 하나씩 검사합니다.
    for message_index, message in enumerate(value, start=1):
        # 각 메시지가 딕셔너리인지 확인합니다.
        if not isinstance(message, dict):
            raise ValueError(
                f"{line_number}번째 줄 {field_name}의 "
                f"{message_index}번째 메시지는 객체여야 합니다."
            )

        # role과 content 키가 모두 있는지 확인합니다.
        if "role" not in message or "content" not in message:
            raise ValueError(
                f"{line_number}번째 줄 {field_name}의 메시지에 "
                "role 또는 content가 없습니다."
            )

        # content가 빈 문자열이 아닌지 확인합니다.
        if not str(message["content"]).strip():
            raise ValueError(
                f"{line_number}번째 줄 {field_name}의 content가 비어 있습니다."
            )


def main() -> None:
    """
    전체 파일을 읽어 DPO 데이터 구조와 중복 여부를 검사합니다.
    """

    # 명령행 인자를 읽습니다.
    args = parse_args()

    # 파일이 실제로 존재하는지 확인합니다.
    if not args.file.exists():
        raise FileNotFoundError(f"파일이 없습니다: {args.file}")

    # 중복 질문 검사를 위한 집합을 생성합니다.
    seen_prompts: set[str] = set()

    # 정상 데이터 개수를 초기화합니다.
    valid_count = 0

    # UTF-8 인코딩으로 파일을 엽니다.
    with args.file.open("r", encoding="utf-8") as file:
        # 줄 번호와 함께 한 줄씩 읽습니다.
        for line_number, line in enumerate(file, start=1):
            # 빈 줄은 건너뜁니다.
            if not line.strip():
                continue

            try:
                # JSON 문자열을 파이썬 딕셔너리로 변환합니다.
                row = json.loads(line)
            except json.JSONDecodeError as error:
                # JSON 문법 오류가 발생한 줄 번호를 포함해 예외를 발생시킵니다.
                raise ValueError(
                    f"{line_number}번째 줄의 JSON 문법이 잘못되었습니다."
                ) from error

            # 필수 필드 목록을 반복합니다.
            for field_name in ("prompt", "chosen", "rejected"):
                # 필수 필드가 누락되었는지 확인합니다.
                if field_name not in row:
                    raise ValueError(
                        f"{line_number}번째 줄에 {field_name}이 없습니다."
                    )

                # 메시지 목록 구조를 검사합니다.
                validate_messages(row[field_name], field_name, line_number)

            # chosen과 rejected 답변 문자열을 가져옵니다.
            chosen_text = str(row["chosen"][-1]["content"]).strip()
            rejected_text = str(row["rejected"][-1]["content"]).strip()

            # 두 답변이 같으면 선호 학습이 불가능하므로 오류를 발생시킵니다.
            if chosen_text == rejected_text:
                raise ValueError(
                    f"{line_number}번째 줄의 chosen과 rejected가 같습니다."
                )

            # 질문 메시지를 안정적인 JSON 문자열로 변환합니다.
            prompt_key = json.dumps(
                row["prompt"],
                ensure_ascii=False,
                sort_keys=True,
            )

            # 같은 질문이 중복되었는지 확인합니다.
            if prompt_key in seen_prompts:
                raise ValueError(
                    f"{line_number}번째 줄의 prompt가 이전 데이터와 중복됩니다."
                )

            # 현재 질문을 중복 검사 집합에 추가합니다.
            seen_prompts.add(prompt_key)

            # 정상 데이터 수를 증가시킵니다.
            valid_count += 1

    # 검증이 완료된 데이터 개수를 출력합니다.
    print(f"검증 완료: {valid_count}개 데이터가 정상입니다.")


# 이 파일을 직접 실행한 경우에만 main 함수를 호출합니다.
if __name__ == "__main__":
    main()
