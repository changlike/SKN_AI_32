# -*- coding: utf-8 -*-
"""요약 보고서 만들기: 고객 문의(cs_inquiries.csv) 집계·서술·저장 파이프라인입니다.

exec_sales_report.py와 동일한 구조를 재사용합니다.
  - 카테고리별/채널별 건수는 코드가 정확히 집계한 확정 수치(facts)입니다.
  - LLM은 이 확정 수치와 문의 원문 샘플만 근거로 요약을 서술하고, 숫자를 새로 만들지 않습니다.
  - LLM 호출이 실패해도 코드 기반 폴백 보고서로 항상 응답합니다.
"""

# datetime은 보고서 저장 헤더와 파일명에 생성 시각을 사용합니다.
import datetime
# Path는 저장 경로를 다룹니다.
from pathlib import Path
# Literal은 공급자 값을 openai 또는 gemini로 제한합니다.
from typing import Literal, Optional

# pandas는 문의 CSV를 DataFrame으로 읽고 집계합니다.
import pandas as pd

# 공용 LLM 생성 함수를 가져옵니다.
from app.core.common import get_chat
from app.core.logging_config import setup_logging
# 데이터/프로젝트 루트 경로를 가져옵니다.
from app.core.settings import DATA_DIR, PROJECT_ROOT
# 공급자별 응답 content를 문자열로 통일하는 유틸을 가져옵니다.
from app.services.llm_response import extract_text

# 공용 로거를 모듈 로드 시 한 번 초기화합니다.
logger = setup_logging()

# 보고서 저장 위치는 매출 보고서와 동일한 reports 폴더를 공유합니다.
REPORTS_DIR = PROJECT_ROOT / "reports"
# 분석 대상 CSV 경로입니다.
DEFAULT_INQUIRY_PATH = DATA_DIR / "cs_inquiries.csv"
# LLM에게 원문 근거로 보여줄 이슈성 카테고리입니다 (개선 논의가 필요한 유형).
ISSUE_CATEGORIES = {"불만", "환불", "교환"}
# 카테고리별로 LLM에 제공할 샘플 문의 최대 개수입니다.
SAMPLES_PER_CATEGORY = 2


def _read_inquiry_dataframe(csv_path: Path = DEFAULT_INQUIRY_PATH) -> pd.DataFrame:
    """문의 CSV를 읽고 기본 유효성을 검사한 DataFrame을 반환합니다."""
    # 파일이 없으면 명확한 경로와 함께 오류를 발생시킵니다.
    if not csv_path.exists():
        raise FileNotFoundError(f"문의 데이터 파일을 찾지 못했습니다: {csv_path}")
    # BOM 포함 한글 CSV도 정상 처리하도록 utf-8-sig 인코딩을 사용합니다.
    dataframe = pd.read_csv(csv_path, encoding="utf-8-sig")
    # 데이터가 비어 있으면 집계할 수 없습니다.
    if dataframe.empty:
        raise ValueError("문의 데이터가 비어 있습니다.")
    # 집계에 필요한 필수 컬럼을 검사합니다.
    required_columns = {"category_hint", "channel", "content"}
    missing = sorted(required_columns - set(dataframe.columns))
    # 누락 컬럼이 있으면 현재 컬럼 목록과 함께 원인을 알립니다.
    if missing:
        raise ValueError(f"필수 컬럼이 누락되었습니다: {missing} / 현재 컬럼: {list(dataframe.columns)}")
    # 검증을 통과한 데이터프레임을 반환합니다.
    return dataframe


def _build_facts(dataframe: pd.DataFrame) -> dict:
    """카테고리별/채널별 집계와 이슈 샘플 원문을 확정 facts로 만듭니다."""
    # 전체 문의 건수를 계산합니다.
    total_count = int(len(dataframe))
    # category_hint별 건수를 큰 값부터 내림차순으로 집계합니다.
    by_category = dataframe["category_hint"].value_counts().to_dict()
    # channel별 건수를 큰 값부터 내림차순으로 집계합니다.
    by_channel = dataframe["channel"].value_counts().to_dict()
    # 건수가 가장 많은 카테고리와 비중(%)을 계산합니다.
    top_category = max(by_category, key=by_category.get)
    top_category_count = int(by_category[top_category])
    top_category_pct = round(top_category_count / total_count * 100, 1)
    # 불만/환불/교환처럼 개선 논의가 필요한 카테고리의 원문 샘플을 모읍니다.
    samples: list[dict] = []
    # 이슈 카테고리를 순서대로 순회합니다.
    for category in ISSUE_CATEGORIES:
        # 해당 카테고리 문의만 추출하고, 완전히 동일한 문구는 하나로 취급합니다.
        subset = dataframe[dataframe["category_hint"] == category].drop_duplicates(subset="content")
        # 카테고리별 최대 개수만큼 앞에서부터 샘플을 가져옵니다.
        for _, row in subset.head(SAMPLES_PER_CATEGORY).iterrows():
            # 카테고리와 원문 내용을 함께 기록합니다.
            samples.append({"category": category, "content": str(row["content"])})
    # 집계와 샘플을 하나의 딕셔너리로 확정합니다.
    return {
        "total_count": total_count,
        "by_category": {str(key): int(value) for key, value in by_category.items()},
        "by_channel": {str(key): int(value) for key, value in by_channel.items()},
        "top_category": str(top_category),
        "top_category_count": top_category_count,
        "top_category_pct": top_category_pct,
        "samples": samples,
    }


def load_facts(csv_path: Path = DEFAULT_INQUIRY_PATH) -> dict:
    """문의 CSV 전체를 집계한 facts를 반환합니다."""
    # 공통 CSV 읽기와 검증 함수를 호출합니다.
    dataframe = _read_inquiry_dataframe(csv_path)
    # 집계 함수를 호출해 facts를 만듭니다.
    return _build_facts(dataframe)


def format_facts(facts: dict) -> str:
    """확정 수치와 샘플 원문을 프롬프트에서 재사용할 문자열로 변환합니다."""
    # 카테고리별 집계를 마크다운 목록 형식으로 만듭니다.
    category_lines = "\n".join(f"- {name}: {count}건" for name, count in facts["by_category"].items())
    # 채널별 집계를 마크다운 목록 형식으로 만듭니다.
    channel_lines = "\n".join(f"- {name}: {count}건" for name, count in facts["by_channel"].items())
    # 이슈 카테고리 원문 샘플을 번호 목록으로 만듭니다.
    sample_lines = "\n".join(
        f"{index}. [{sample['category']}] {sample['content']}"
        for index, sample in enumerate(facts["samples"], start=1)
    )
    # LLM이 집계를 새로 계산하지 않도록 숫자를 모두 미리 계산해 제공합니다.
    return (
        f"- 총 문의 건수: {facts['total_count']}건\n"
        f"- 최다 유형: {facts['top_category']} ({facts['top_category_count']}건, {facts['top_category_pct']}%)\n"
        f"[카테고리별 건수]\n{category_lines}\n\n"
        f"[채널별 건수]\n{channel_lines}\n\n"
        f"[개선 논의가 필요한 문의 원문 샘플]\n{sample_lines}"
    )


# write_report 함수는 provider를 인자로 받아 매출 보고서와 동일한 방식으로 모델을 생성합니다.
def write_report(facts: dict, provider: Literal["openai", "gemini"]) -> str:
    """확정 facts와 원문 샘플만 근거로 한국어 문의 요약 보고서를 작성합니다."""
    # 요청으로 전달된 공급자와 temperature 0.3으로 LangChain 모델을 생성합니다.
    llm = get_chat(provider=provider, temperature=0.3)
    # 집계 수치는 그대로 쓰고, 원문 샘플에서만 주제를 요약하도록 제한합니다.
    prompt = (
        "너는 온라인 쇼핑몰 CS 운영 담당자다. 아래 [확정 수치]와 [문의 원문 샘플]만 근거로 "
        "실무진용 한국어 고객 문의 요약 보고서를 마크다운으로 작성하라. "
        "주어진 건수를 변경하거나 새로운 수치를 계산·추측·창작하지 마라. "
        "원문에 없는 원인을 단정하지 말고 샘플에서 관찰되는 경향이라고 표현하라. "
        "반드시 '## 문의 현황 요약', '## 주요 이슈', '## 개선 제안' 세 섹션을 포함하라.\n\n"
        f"[확정 수치]\n{format_facts(facts)}"
    )
    # 모델에 프롬프트를 전달하고 응답 객체를 받습니다.
    response = llm.invoke(prompt)
    # 공급자별 응답 형식 차이를 공통 문자열로 변환합니다.
    return extract_text(response)


def make_fallback_report(facts: dict, reason: str = "") -> str:
    """API 호출이 불가능할 때도 확정 수치만으로 기본 보고서를 생성합니다."""
    # 카테고리별 집계를 목록 문자열로 만듭니다.
    category_lines = "\n".join(f"- {name}: {count}건" for name, count in facts["by_category"].items())
    # LLM 없이도 숫자를 바꾸지 않는 재현 가능한 보고서를 작성합니다.
    body = (
        "## 문의 현황 요약\n"
        f"전체 문의는 {facts['total_count']}건이며, 이 중 {facts['top_category']} 유형이 "
        f"{facts['top_category_count']}건({facts['top_category_pct']}%)으로 가장 많았습니다.\n\n"
        "## 주요 이슈\n"
        f"카테고리별 분포는 다음과 같습니다.\n{category_lines}\n\n"
        "## 개선 제안\n"
        "비중이 높은 유형을 우선순위로 두고 담당 부서와 원문 샘플을 함께 검토합니다."
    )
    # 실패 이유가 있으면 문서 하단에 자동 대체 보고서임을 표시합니다.
    if reason:
        body += f"\n\n> LLM 호출 실패로 기본 템플릿을 사용했습니다: {reason}"
    # 완성된 기본 보고서를 반환합니다.
    return body


# write_report_with_fallback 함수도 provider를 인자로 받아 write_report에 그대로 전달합니다.
def write_report_with_fallback(facts: dict, provider: Literal["openai", "gemini"]) -> str:
    """LLM 보고서 생성을 시도하고 실패하면 코드 기반 보고서로 대체합니다."""
    try:
        # 우선 선택한 OpenAI 또는 Gemini 모델로 자연어 보고서를 만듭니다.
        return write_report(facts, provider)
    except Exception as error:
        # API 키, 네트워크, 할당량 문제로 실패해도 앱이 종료되지 않도록 폴백합니다.
        logger.exception("문의 요약 보고서 LLM 생성 실패: provider=%s", provider)
        return make_fallback_report(facts, f"{type(error).__name__}: {error}")


def save_report(body: str, filename: Optional[str] = None) -> Path:
    """보고서를 UTF-8 마크다운 파일로 저장하고 경로를 반환합니다."""
    # reports 폴더가 없을 때 자동으로 생성합니다.
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    # 별도 파일명이 없으면 생성 시각 기준 표준 이름을 사용합니다.
    report_name = filename or f"inquiry_summary_{datetime.datetime.now():%Y%m%d_%H%M%S}.md"
    # 저장 대상 전체 경로를 구성합니다.
    report_path = REPORTS_DIR / report_name
    # 문서 제목과 자동 생성일을 헤더에 기록합니다.
    header = f"# 고객 문의 요약 보고서\n\n> 생성일: {datetime.date.today().isoformat()} / 자동 생성\n\n"
    # 한글이 보존되도록 UTF-8로 전체 문서를 저장합니다.
    report_path.write_text(header + body.strip() + "\n", encoding="utf-8")
    # 저장 완료를 구조적 로그로 남깁니다.
    logger.info("문의 요약 보고서 저장 완료: path=%s", report_path)
    # 호출부가 저장 결과를 응답하거나 후속 처리할 수 있도록 경로를 반환합니다.
    return report_path


# generate_summary_report 함수는 집계→서술→저장을 한 번에 실행하는 진입점입니다.
def generate_summary_report(provider: Literal["openai", "gemini"]) -> dict:
    """집계→LLM 서술→마크다운 저장을 한 번에 실행하고 API 응답용 dict를 반환합니다."""
    # 문의 CSV 전체를 집계합니다.
    facts = load_facts()
    # API 장애까지 고려한 안전한 보고서 생성 함수를 사용합니다.
    body = write_report_with_fallback(facts, provider)
    # 완성된 보고서를 저장합니다.
    report_path = save_report(body)
    # 라우터가 그대로 응답 스키마에 채울 수 있도록 facts와 결과를 합쳐 반환합니다.
    return {**facts, "report_markdown": body, "saved_path": str(report_path)}
