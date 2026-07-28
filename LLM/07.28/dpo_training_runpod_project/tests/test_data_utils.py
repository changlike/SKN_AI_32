"""DPO 데이터 검증 함수의 기본 동작을 확인합니다."""

from src.data_utils import validate_record


def test_valid_record_has_no_errors() -> None:
    """정상 레코드는 오류 목록이 비어 있어야 합니다."""

    record = {"prompt": "질문", "chosen": "좋은 답", "rejected": "나쁜 답"}
    assert validate_record(record, 1) == []


def test_same_chosen_and_rejected_is_invalid() -> None:
    """chosen과 rejected가 같으면 오류가 발생해야 합니다."""

    record = {"prompt": "질문", "chosen": "같은 답", "rejected": "같은 답"}
    errors = validate_record(record, 1)
    assert any("동일" in error for error in errors)
