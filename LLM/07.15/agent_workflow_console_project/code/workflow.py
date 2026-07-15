# -*- coding: utf-8 -*-
"""LangGraph 기반 CS 티켓 처리 워크플로우의 핵심 기능을 정의합니다."""

# 타입이 정해진 딕셔너리 상태를 만들기 위해 TypedDict와 NotRequired를 가져옵니다.
from typing import NotRequired, TypedDict

# LangChain 채팅 모델에 전달할 시스템 메시지와 사용자 메시지를 가져옵니다.
from langchain_core.messages import HumanMessage, SystemMessage

# 상태 기반 그래프와 시작/종료 가상 노드를 가져옵니다.
from langgraph.graph import END, START, StateGraph

# 공통 모듈의 채팅 모델 생성 함수를 가져옵니다.
from common import get_chat


# API와 그래프에 의존하지 않는 순수 파이썬 규칙 함수를 가져옵니다.
from rules import (
    CATEGORIES,
    calculate_priority,
    calculate_route,
    calculate_team,
    normalize_category,
)


class TicketState(TypedDict):
    """모든 노드가 공유하며 단계별 결과를 누적하는 상태 스키마입니다."""

    # 사용자가 입력한 CS 티켓 원문입니다.
    content: str

    # 분류 노드가 채우는 카테고리 값입니다.
    category: NotRequired[str]

    # 우선순위 노드가 채우는 긴급도 값입니다.
    priority: NotRequired[str]

    # 배정 또는 에스컬레이션 노드가 채우는 담당팀입니다.
    team: NotRequired[str]

    # 조건부 분기 실습에서 어떤 경로를 선택했는지 기록합니다.
    route: NotRequired[str]

    # 조건부 분기 실습에서 후속 조치 내용을 기록합니다.
    action: NotRequired[str]

    # 검증 실패 또는 API 예외 내용을 기록합니다.
    error: NotRequired[str]


def message_to_text(response: object) -> str:
    """LangChain 공급자별 응답 형식을 안전하게 일반 문자열로 변환합니다."""

    # 대부분의 LangChain AIMessage는 content 속성에 최종 응답을 저장합니다.
    content = getattr(response, "content", response)

    # 일반 문자열이면 앞뒤 공백을 제거해 바로 반환합니다.
    if isinstance(content, str):
        return content.strip()

    # 일부 모델은 여러 콘텐츠 블록을 리스트로 반환할 수 있습니다.
    if isinstance(content, list):
        # 최종 문자열 조각을 순서대로 모을 임시 리스트입니다.
        text_parts: list[str] = []

        # 리스트에 포함된 각 콘텐츠 블록을 차례로 확인합니다.
        for item in content:
            # 블록이 딕셔너리이고 text 키가 있으면 실제 텍스트만 추가합니다.
            if isinstance(item, dict) and "text" in item:
                text_parts.append(str(item["text"]))
            # 다른 형식은 정보 유실을 막기 위해 문자열로 변환하여 추가합니다.
            else:
                text_parts.append(str(item))

        # 여러 조각을 하나의 문장으로 합치고 앞뒤 공백을 제거합니다.
        return " ".join(text_parts).strip()

    # 예상하지 못한 형식도 프로그램이 중단되지 않도록 문자열로 변환합니다.
    return str(content).strip()



def make_classify_node(provider: str):
    """선택한 LLM 공급자를 사용하는 분류 노드 함수를 생성합니다."""

    # 같은 입력의 결과 변동을 줄이기 위해 temperature를 0으로 설정합니다.
    llm = get_chat(provider=provider, temperature=0.0)

    def classify_node(state: TicketState) -> dict:
        """티켓 내용을 LLM으로 분류하고 출력값을 허용 목록으로 검증합니다."""

        # 티켓 내용이 없을 수도 있으므로 get과 기본값으로 안전하게 읽습니다.
        content = state.get("content", "").strip()

        # 빈 입력은 불필요한 API 호출 없이 기타로 보정하고 오류를 기록합니다.
        if not content:
            return {"category": "기타", "error": "빈 티켓 내용 → 기타 보정"}

        # 모델의 역할과 출력 형식을 강제하는 시스템 메시지를 작성합니다.
        system_message = SystemMessage(
            content=(
                f"다음 CS 티켓을 {CATEGORIES} 중 정확히 하나로 분류하세요. "
                "설명 없이 카테고리 단어만 출력하세요."
            )
        )

        # 실제 사용자가 입력한 티켓 내용을 HumanMessage로 작성합니다.
        human_message = HumanMessage(content=content)

        try:
            # 시스템 메시지와 사용자 메시지를 모델에 전달하여 분류 결과를 받습니다.
            response = llm.invoke([system_message, human_message])

            # 공급자별 응답 구조 차이를 흡수하여 일반 문자열로 변환합니다.
            raw_output = message_to_text(response)

            # 허용 목록 검증과 부분 매칭 보정을 수행합니다.
            category, error = normalize_category(raw_output)

            # 이번 노드가 채운 필드만 반환하면 LangGraph가 기존 상태에 병합합니다.
            return {"category": category, "error": error}
        except Exception as exc:
            # API 호출 실패가 전체 배치를 중단시키지 않도록 기타로 폴백합니다.
            return {"category": "기타", "error": f"분류 API 예외: {type(exc).__name__}: {exc}"}

    # 공급자가 연결된 실제 분류 노드 함수를 호출자에게 반환합니다.
    return classify_node


def priority_node(state: TicketState) -> dict:
    """카테고리와 키워드를 이용해 LLM 없이 우선순위를 계산합니다."""

    # 입력 티켓 내용을 안전하게 문자열로 읽습니다.
    text = state.get("content", "")

    # 이전 분류 노드가 채운 카테고리를 읽되 없으면 기타로 처리합니다.
    category = state.get("category", "기타")

    # 외부 의존성이 없는 공통 규칙 함수로 우선순위를 계산합니다.
    priority = calculate_priority(text, category)

    # 새로 계산한 priority 필드만 상태 업데이트 값으로 반환합니다.
    return {"priority": priority}


def assign_node(state: TicketState) -> dict:
    """카테고리별 담당팀 매핑 규칙으로 팀을 배정합니다."""

    # 분류 결과가 없거나 매핑에 없을 때를 대비해 기본값 기타를 사용합니다.
    category = state.get("category", "기타")

    # 외부 의존성이 없는 공통 규칙 함수로 담당팀을 계산합니다.
    team = calculate_team(category)

    # 배정 결과인 team 필드만 반환합니다.
    return {"team": team}


def route_by_priority(state: TicketState) -> str:
    """우선순위를 읽어 긴급 경로 또는 일반 배정 경로 이름을 반환합니다."""

    # 외부 의존성이 없는 공통 라우팅 함수로 다음 노드 이름을 결정합니다.
    return calculate_route(state.get("priority", "보통"))


def escalate_node(state: TicketState) -> dict:
    """긴급 티켓을 긴급대응팀으로 즉시 에스컬레이션합니다."""

    # 긴급 경로에서 필요한 담당팀, 경로명, 후속 조치를 한 번에 반환합니다.
    return {
        "team": "긴급대응팀",
        "route": "긴급에스컬",
        "action": "SLA 30분 내 즉시 에스컬레이션(담당자 호출)",
    }


def assign_route_node(state: TicketState) -> dict:
    """일반 티켓을 카테고리 규칙에 따라 배정하고 SLA 정보를 추가합니다."""

    # 중복 구현을 피하기 위해 기존 assign_node 함수를 재사용합니다.
    update = assign_node(state)

    # 조건부 분기 결과를 확인할 수 있도록 일반배정 경로명을 추가합니다.
    update["route"] = "일반배정"

    # 이미 계산된 팀 이름을 이용하여 후속 조치 문장을 생성합니다.
    update["action"] = f"{update['team']} 일반 배정(SLA 24시간)"

    # 팀, 경로, 조치가 담긴 부분 상태를 반환합니다.
    return update


def build_linear_workflow(provider: str):
    """분류 → 우선순위 → 배정 순서가 고정된 선형 워크플로우를 만듭니다."""

    # TicketState 스키마를 공유 상태로 사용하는 그래프 빌더를 생성합니다.
    graph_builder = StateGraph(TicketState)

    # 선택한 공급자를 사용하는 분류 노드를 classify라는 이름으로 등록합니다.
    graph_builder.add_node("classify", make_classify_node(provider))

    # 규칙 기반 우선순위 노드를 priority라는 이름으로 등록합니다.
    graph_builder.add_node("priority", priority_node)

    # 규칙 기반 팀 배정 노드를 assign이라는 이름으로 등록합니다.
    graph_builder.add_node("assign", assign_node)

    # 시작 지점 다음에 반드시 분류 노드가 실행되도록 연결합니다.
    graph_builder.add_edge(START, "classify")

    # 분류 다음에 반드시 우선순위 노드가 실행되도록 연결합니다.
    graph_builder.add_edge("classify", "priority")

    # 우선순위 다음에 반드시 배정 노드가 실행되도록 연결합니다.
    graph_builder.add_edge("priority", "assign")

    # 배정이 끝나면 워크플로우를 종료하도록 연결합니다.
    graph_builder.add_edge("assign", END)

    # 선언한 노드와 엣지를 실제 실행 가능한 그래프로 컴파일하여 반환합니다.
    return graph_builder.compile()


def build_conditional_workflow(provider: str):
    """긴급 티켓과 일반 티켓이 서로 다른 경로를 타는 조건부 워크플로우를 만듭니다."""

    # TicketState를 공유 상태로 사용하는 새 그래프 빌더를 생성합니다.
    graph_builder = StateGraph(TicketState)

    # LLM 기반 분류 노드를 등록합니다.
    graph_builder.add_node("classify", make_classify_node(provider))

    # 규칙 기반 우선순위 노드를 등록합니다.
    graph_builder.add_node("priority", priority_node)

    # 긴급 티켓을 처리할 에스컬레이션 노드를 등록합니다.
    graph_builder.add_node("escalate", escalate_node)

    # 일반 티켓을 처리할 일반 배정 노드를 등록합니다.
    graph_builder.add_node("assign", assign_route_node)

    # 시작에서 분류까지의 고정 엣지를 연결합니다.
    graph_builder.add_edge(START, "classify")

    # 분류에서 우선순위까지의 고정 엣지를 연결합니다.
    graph_builder.add_edge("classify", "priority")

    # priority 다음 노드는 route_by_priority의 반환값에 따라 동적으로 선택합니다.
    graph_builder.add_conditional_edges(
        "priority",
        route_by_priority,
        {"escalate": "escalate", "assign": "assign"},
    )

    # 긴급 경로 처리가 끝나면 그래프를 종료합니다.
    graph_builder.add_edge("escalate", END)

    # 일반 경로 처리가 끝나면 그래프를 종료합니다.
    graph_builder.add_edge("assign", END)

    # 조건부 분기가 포함된 실행 가능한 그래프를 반환합니다.
    return graph_builder.compile()
