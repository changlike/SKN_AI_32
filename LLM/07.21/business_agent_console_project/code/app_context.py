# -*- coding: utf-8 -*-
"""콘솔 앱 전체에서 선택한 LLM 공급자를 보관하는 상태 모듈입니다."""

# 사용자가 선택한 공급자를 문자열로 저장합니다.
# 초기값은 OpenAI이지만 main.py 시작 시 공급자 선택 메뉴에서 다시 지정됩니다.
_PROVIDER: str = "openai"


def set_provider(provider: str) -> None:
    """OpenAI 또는 Gemini 중 사용자가 선택한 공급자를 저장합니다."""
    # 허용된 값만 상태에 저장해 잘못된 모델 이름이 뒤 단계로 전달되지 않게 합니다.
    if provider not in {"openai", "gemini"}:
        # 잘못된 값은 즉시 ValueError로 알리고 조용한 오동작을 방지합니다.
        raise ValueError("provider는 'openai' 또는 'gemini'만 사용할 수 있습니다.")
    # 모듈 전역 변수를 변경한다는 사실을 명시합니다.
    global _PROVIDER
    # 검증을 통과한 공급자를 현재 선택값으로 저장합니다.
    _PROVIDER = provider


def get_provider() -> str:
    """현재 선택된 LLM 공급자 문자열을 반환합니다."""
    # 다른 서비스 모듈은 이 함수를 호출해 동일한 공급자를 공유합니다.
    return _PROVIDER


def get_provider_label() -> str:
    """콘솔에 표시할 한글 공급자 이름을 반환합니다."""
    # 내부 문자열을 사용자가 읽기 쉬운 표시 이름으로 변환합니다.
    return "OpenAI" if _PROVIDER == "openai" else "Google Gemini"
