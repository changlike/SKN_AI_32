# -*- coding: utf-8 -*-
"""도구를 생각하고 실행하고 관찰하는 ReAct 패턴의 전문 에이전트입니다."""

# threading.Lock은 공급자별 에이전트 중복 생성을 방지합니다.
from threading import Lock
# typing.Literal은 허용 공급자를 제한합니다.
from typing import Literal

# create_agent는 최신 LangChain의 production-ready ReAct 도구 루프를 만듭니다.
from langchain.agents import create_agent
# InMemorySaver는 thread_id별 대화 상태를 메모리에 저장합니다.
from langgraph.checkpoint.memory import InMemorySaver

# 전체 비즈니스 도구와 공급자 ContextVar를 가져옵니다.
from app.agents.tools import ALL_TOOLS, current_provider
# 채팅 모델 팩토리를 가져옵니다.
from app.services.llm_factory import create_chat_model

# SYSTEM_PROMPT는 ReAct 에이전트의 역할과 안전 규칙을 정의합니다.
SYSTEM_PROMPT = """
너는 승승장구몰 통합 CS 상담원이다. 반드시 친절한 한국어로 답한다.
질문을 분석하고 필요한 도구를 선택하여 Thought → Action → Observation 방식으로 문제를 해결한다.
주문 상태는 get_order_status, 재고는 get_stock, FAQ는 search_faq를 사용한다.
환불·교환·멤버십 정책은 반드시 policy_search가 반환한 PDF 근거로만 답한다.
고객이 실제 교환 접수를 명시적으로 요청할 때만 request_exchange를 호출한다.
도구가 찾을 수 없다고 반환한 값은 절대로 추측하거나 만들어내지 않는다.
최종 답변에는 내부 추론을 노출하지 말고 확인된 결과와 필요한 안내만 제공한다.
""".strip()

# _agent_lock은 공급자별 에이전트 생성 구간을 보호합니다.
_agent_lock = Lock()
# _agents는 OpenAI와 Gemini 에이전트를 각각 캐시합니다.
_agents: dict[str, object] = {}
# _memory는 모든 에이전트가 thread_id별 대화를 기억하는 체크포인터입니다.
_memory = InMemorySaver()


# get_react_agent 함수는 공급자별 ReAct 에이전트를 한 번만 생성합니다.
def get_react_agent(provider: Literal["openai", "gemini"]):
    """도구 5개와 단기 메모리를 결합한 ReAct 에이전트를 반환합니다."""
    # 이미 생성된 공급자의 에이전트가 있으면 즉시 반환합니다.
    if provider in _agents:
        # 캐시된 에이전트를 재사용합니다.
        return _agents[provider]
    # 동시 생성을 막기 위해 잠금을 획득합니다.
    with _agent_lock:
        # 잠금 대기 중 생성 여부를 다시 확인합니다.
        if provider not in _agents:
            # 선택한 공급자의 LLM 객체를 생성합니다.
            model = create_chat_model(provider)
            # 최신 create_agent로 도구 호출 루프와 메모리를 결합합니다.
            _agents[provider] = create_agent(
                model=model,
                tools=ALL_TOOLS,
                system_prompt=SYSTEM_PROMPT,
                checkpointer=_memory,
            )
    # 생성 또는 캐시된 에이전트를 반환합니다.
    return _agents[provider]


# invoke_react_agent 함수는 현재 요청의 공급자를 설정하고 에이전트를 호출합니다.
def invoke_react_agent(message: str, thread_id: str, provider: Literal["openai", "gemini"]) -> str:
    """ReAct 에이전트를 호출하여 최종 텍스트 답변을 반환합니다."""
    # 정책 도구가 올바른 임베딩 공급자를 사용하도록 ContextVar 값을 설정합니다.
    token = current_provider.set(provider)
    # 예외가 나도 ContextVar가 반드시 복구되도록 try-finally를 사용합니다.
    try:
        # 공급자별 ReAct 에이전트를 가져옵니다.
        agent = get_react_agent(provider)
        # 동일 thread_id가 같은 대화 메모리를 사용하도록 configurable을 지정합니다.
        result = agent.invoke(
            {"messages": [{"role": "user", "content": message}]},
            config={"configurable": {"thread_id": thread_id}},
        )
        # 에이전트 결과의 마지막 메시지를 가져옵니다.
        final_message = result["messages"][-1]
        # 메시지 content를 문자열로 변환해 반환합니다.
        return str(final_message.content)
    finally:
        # 다음 요청에 공급자 값이 섞이지 않도록 이전 ContextVar 상태를 복원합니다.
        current_provider.reset(token)
