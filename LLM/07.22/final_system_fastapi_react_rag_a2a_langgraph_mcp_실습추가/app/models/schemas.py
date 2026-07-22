# -*- coding: utf-8 -*-
"""FastAPI 요청 및 응답에 사용하는 Pydantic 스키마 모듈입니다."""

# typing.Any는 실행 추적 정보처럼 다양한 타입의 값을 허용합니다.
from typing import Any, Literal

# BaseModel은 JSON 요청과 응답을 검증하는 기본 클래스입니다.
from pydantic import BaseModel, Field


# ChatRequest는 통합 에이전트 질문 API의 입력 구조입니다.
class ChatRequest(BaseModel):
    """사용자 질문과 세션 정보를 전달하는 요청 모델입니다."""

    # message는 에이전트가 처리할 자연어 질문입니다.
    message: str = Field(min_length=1, description="사용자 질문")
    # thread_id는 LangGraph 메모리에서 대화 세션을 구분합니다.
    thread_id: str = Field(default="web-user", min_length=1, description="대화 세션 ID")
    # provider는 이번 요청에서 사용할 LLM 공급자입니다.
    provider: Literal["openai", "gemini"] = Field(default="openai")


# ChatResponse는 최종 답변과 워크플로우 실행 정보를 반환합니다.
class ChatResponse(BaseModel):
    """통합 워크플로우의 최종 결과 모델입니다."""

    # answer는 사용자에게 보여 줄 최종 한국어 답변입니다.
    answer: str
    # provider는 실제 사용된 모델 공급자입니다.
    provider: str
    # thread_id는 응답이 속한 대화 세션입니다.
    thread_id: str
    # route는 분류기가 선택한 처리 경로입니다.
    route: str
    # trace는 ReAct, RAG, A2A, LangGraph, MCP 단계 실행 기록입니다.
    trace: list[dict[str, Any]] = Field(default_factory=list)


# ToolRequest는 개별 데이터 도구 테스트에 사용하는 공통 입력 모델입니다.
class ToolRequest(BaseModel):
    """도구 이름과 도구 인자를 전달하는 요청 모델입니다."""

    # tool_name은 실행할 도구의 고유 이름입니다.
    tool_name: Literal["get_order_status", "get_stock", "search_faq", "request_exchange"]
    # arguments는 각 도구에 필요한 키-값 인자입니다.
    arguments: dict[str, Any] = Field(default_factory=dict)


# ToolResponse는 MCP 또는 로컬 도구 실행 결과를 반환합니다.
class ToolResponse(BaseModel):
    """도구 실행 결과와 오류 상태를 반환하는 모델입니다."""

    # success는 도구 실행 성공 여부입니다.
    success: bool
    # tool_name은 실행한 도구 이름입니다.
    tool_name: str
    # result는 도구가 생성한 문자열 결과입니다.
    result: str


# ComplaintRequest는 문의 처리 연계 부서 연결 탭의 입력 구조입니다.
class ComplaintRequest(BaseModel):
    """고객 문의를 담당 부서 접수 API로 전달하는 요청 모델입니다."""

    # customer_id는 문의를 남긴 고객의 식별자입니다.
    customer_id: str = Field(min_length=1, description="고객 아이디")
    # message는 고객이 입력한 문의 원문입니다.
    message: str = Field(min_length=1, description="문의 내용")


# ComplaintResponse는 담당 부서 접수 처리 결과를 반환합니다.
class ComplaintResponse(BaseModel):
    """실행 질문 감지 및 DB 접수 결과 모델입니다."""

    # matched는 교환/환불 같은 실행 질문으로 인식되었는지 여부입니다.
    matched: bool
    # answer는 사용자에게 보여 줄 응답 문구입니다.
    answer: str
    # dept_id는 배정된 담당 부서 아이디이며, 미매칭 시 None입니다.
    dept_id: str | None = None
    # cc_id는 customer_complaint 테이블에 생성된 접수 번호이며, 미매칭 시 None입니다.
    cc_id: int | None = None


# InquirySummaryReportRequest는 요약 보고서 만들기 탭의 입력 구조입니다.
class InquirySummaryReportRequest(BaseModel):
    """요약 보고서 서술에 사용할 LLM 공급자를 전달하는 요청 모델입니다."""

    # provider는 보고서 서술에 사용할 LLM 공급자입니다.
    provider: Literal["openai", "gemini"] = Field(default="openai")


# InquirySummaryReportResponse는 문의 집계 수치와 LLM 서술 보고서를 함께 반환합니다.
class InquirySummaryReportResponse(BaseModel):
    """카테고리·채널별 집계와 마크다운 보고서, 저장 경로를 담는 응답 모델입니다."""

    # total_count는 전체 문의 건수입니다.
    total_count: int
    # by_category는 카테고리별 문의 건수입니다.
    by_category: dict[str, int]
    # by_channel은 채널별 문의 건수입니다.
    by_channel: dict[str, int]
    # top_category는 건수가 가장 많은 카테고리입니다.
    top_category: str
    # top_category_count와 top_category_pct는 최다 카테고리의 건수와 비중(%)입니다.
    top_category_count: int
    top_category_pct: float
    # samples는 LLM이 근거로 사용한 이슈성 문의 원문 샘플입니다.
    samples: list[dict[str, str]]
    # report_markdown은 LLM(또는 폴백 템플릿)이 작성한 보고서 본문입니다.
    report_markdown: str
    # saved_path는 보고서 마크다운 파일이 저장된 서버 경로입니다.
    saved_path: str


# ExecSalesReportRequest는 임원용 매출 보고서 탭의 입력 구조입니다.
class ExecSalesReportRequest(BaseModel):
    """분석 대상 월과 LLM 공급자를 전달하는 요청 모델입니다."""

    # month는 분석할 달("YYYY-MM")이며, 비우면 CSV의 최신 달을 사용합니다.
    month: str | None = Field(default=None, description="분석 대상 월. 예: 2024-04")
    # provider는 보고서 서술에 사용할 LLM 공급자입니다.
    provider: Literal["openai", "gemini"] = Field(default="openai")


# ExecSalesReportResponse는 집계 수치와 LLM 서술 보고서를 함께 반환합니다.
class ExecSalesReportResponse(BaseModel):
    """확정 수치와 마크다운 보고서, 저장 경로를 담는 응답 모델입니다."""

    # month는 분석된 대상 월입니다.
    month: str
    # prev_month는 비교 대상인 전월입니다.
    prev_month: str
    # total은 대상 월의 총매출입니다.
    total: int
    # prev_total은 전월 총매출입니다.
    prev_total: int
    # growth_pct는 전월 대비 증감률(%)입니다.
    growth_pct: float
    # top_category와 top_value는 매출 1위 카테고리와 금액입니다.
    top_category: str
    top_value: int
    # second_category와 second_value는 매출 2위 카테고리와 금액입니다.
    second_category: str
    second_value: int
    # by_category는 전체 카테고리별 매출입니다.
    by_category: dict[str, int]
    # report_markdown은 LLM(또는 폴백 템플릿)이 작성한 보고서 본문입니다.
    report_markdown: str
    # saved_path는 보고서 마크다운 파일이 저장된 서버 경로입니다.
    saved_path: str


# A2AMessageRequest는 에이전트 간 위임 메시지를 표현합니다.
class A2AMessageRequest(BaseModel):
    """A2A 게이트웨이에 전달하는 에이전트 메시지 모델입니다."""

    # target_agent는 작업을 받을 전문 에이전트 이름입니다.
    target_agent: Literal["order-agent", "inventory-agent", "faq-agent", "policy-agent", "exchange-agent"]
    # message는 전문 에이전트가 처리할 사용자 요청입니다.
    message: str = Field(min_length=1)
    # provider는 전문 에이전트가 사용할 LLM 공급자입니다.
    provider: Literal["openai", "gemini"] = Field(default="openai")
    # thread_id는 에이전트 간에도 동일하게 유지할 세션 ID입니다.
    thread_id: str = Field(default="a2a-user")
