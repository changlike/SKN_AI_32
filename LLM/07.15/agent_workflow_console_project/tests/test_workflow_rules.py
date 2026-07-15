# -*- coding: utf-8 -*-
"""외부 API와 LangGraph 없이 순수 파이썬 규칙을 테스트합니다."""

# 테스트 대상 코드 폴더를 import 경로에 추가하기 위해 sys와 pathlib을 가져옵니다.
import pathlib
import sys

# 프로젝트 루트/code 폴더를 파이썬 모듈 검색 경로 앞쪽에 추가합니다.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "code"))

# 외부 패키지 설치 없이 테스트할 순수 규칙 함수들을 가져옵니다.
from rules import calculate_priority, calculate_route, calculate_team, normalize_category


def test_normalize_category_exact_match() -> None:
    """정확한 카테고리 출력은 오류 없이 그대로 채택되어야 합니다."""

    # 정확히 결제라고 입력했을 때 결제와 빈 오류 문자열이 반환되는지 확인합니다.
    assert normalize_category("결제") == ("결제", "")


def test_normalize_category_sentence_match() -> None:
    """설명 문장 안의 허용 카테고리도 추출되어야 합니다."""

    # 문장형 응답에서도 기술지원이라는 허용 단어를 찾아야 합니다.
    assert normalize_category("이 문의는 기술지원으로 보입니다.") == ("기술지원", "")


def test_normalize_category_fallback() -> None:
    """허용 목록 밖 출력은 기타로 보정되고 오류가 기록되어야 합니다."""

    # 허용되지 않은 단어를 입력하여 폴백 결과를 받습니다.
    category, error = normalize_category("제품문의")

    # 안전한 기본 카테고리는 기타여야 합니다.
    assert category == "기타"

    # 보정 이유를 추적할 수 있는 오류 메시지가 있어야 합니다.
    assert "미허용" in error


def test_priority_and_assignment_rules() -> None:
    """결제 티켓은 긴급 우선순위와 결제지원팀으로 처리되어야 합니다."""

    # 결제 오류 문장이 긴급으로 판정되는지 확인합니다.
    assert calculate_priority("결제 오류가 발생합니다.", "결제") == "긴급"

    # 결제 카테고리가 결제지원팀으로 배정되는지 확인합니다.
    assert calculate_team("결제") == "결제지원팀"


def test_conditional_router() -> None:
    """긴급은 escalate, 보통은 assign 경로를 반환해야 합니다."""

    # 긴급 상태가 에스컬레이션 경로를 선택하는지 확인합니다.
    assert calculate_route("긴급") == "escalate"

    # 보통 상태가 일반 배정 경로를 선택하는지 확인합니다.
    assert calculate_route("보통") == "assign"
