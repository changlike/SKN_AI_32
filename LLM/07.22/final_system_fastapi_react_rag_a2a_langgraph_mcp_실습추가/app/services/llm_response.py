# -*- coding: utf-8 -*-
"""공급자별로 다른 LangChain 응답 content 형식을 순수 문자열로 통일하는 유틸입니다."""

# extract_text 함수는 원본 message_utils.py를 찾을 수 없어 react_agent.py의
# `str(final_message.content)` 패턴을 기준으로 방어적으로 재구성한 버전입니다.
def extract_text(response) -> str:
    """AIMessage.content가 문자열이든 파트 리스트든 항상 문자열로 반환합니다."""
    # content 속성이 없는 값이 들어오면 원본 값 자체를 대상으로 처리합니다.
    content = getattr(response, "content", response)
    # OpenAI처럼 이미 순수 문자열이면 그대로 반환합니다.
    if isinstance(content, str):
        # 추가 처리 없이 즉시 반환합니다.
        return content
    # Gemini처럼 파트 리스트로 오는 경우를 대비해 순회하며 텍스트만 모읍니다.
    if isinstance(content, list):
        # 모은 텍스트 조각을 담을 리스트입니다.
        parts: list[str] = []
        # 각 파트를 순회합니다.
        for part in content:
            # {"type": "text", "text": "..."} 형태의 파트를 처리합니다.
            if isinstance(part, dict) and "text" in part:
                # text 키 값을 문자열로 변환해 추가합니다.
                parts.append(str(part["text"]))
            # 파트가 이미 문자열인 경우를 처리합니다.
            elif isinstance(part, str):
                # 문자열 파트를 그대로 추가합니다.
                parts.append(part)
        # 모든 텍스트 조각을 이어 붙여 반환합니다.
        return "".join(parts)
    # 그 외 알 수 없는 형식은 안전하게 문자열 변환만 수행합니다.
    return str(content)
