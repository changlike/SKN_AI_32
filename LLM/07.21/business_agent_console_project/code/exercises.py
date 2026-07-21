# -*- coding: utf-8 -*-
"""제24강 실습문제 해답을 콘솔 메뉴에서 실행하기 위한 모듈입니다."""

from pathlib import Path
import pandas as pd
from common import DATA
from business_service import (
    load_facts,
    load_facts_for_month,
    save_report,
    write_report_with_fallback,
)
from chart_service import make_category_chart


def exercise_1_category_growth_and_chart() -> None:
    """실습 1: 첫 달 대비 마지막 달 카테고리 성장률과 최신 매출 차트를 생성합니다."""
    # 실습에서 사용할 monthly_sales.csv 경로를 지정합니다.
    csv_path = DATA / "monthly_sales.csv"
    # 파일이 없으면 친절한 안내 후 종료합니다.
    if not csv_path.exists():
        print(f"[실패] 파일을 찾을 수 없습니다: {csv_path}")
        return
    # 월 순서를 보장하도록 CSV를 읽고 정렬합니다.
    dataframe = pd.read_csv(csv_path, encoding="utf-8-sig").sort_values("month").reset_index(drop=True)
    # 첫 달과 마지막 달 데이터 행을 선택합니다.
    first = dataframe.iloc[0]
    last = dataframe.iloc[-1]
    # month와 total을 제외한 동적 카테고리 컬럼 목록을 만듭니다.
    categories = [column for column in dataframe.columns if column not in {"month", "total"}]
    # 카테고리별 성장률을 담을 빈 딕셔너리를 만듭니다.
    growth: dict[str, float] = {}
    # 모든 카테고리를 순회하며 첫 달 대비 마지막 달 성장률을 계산합니다.
    for category in categories:
        # 첫 달 값이 0이면 0으로 나누기가 되므로 해당 카테고리를 건너뜁니다.
        if float(first[category]) == 0:
            continue
        # 성장률 공식을 코드로 정확히 계산하고 소수점 한 자리로 반올림합니다.
        growth[category] = round((float(last[category]) - float(first[category])) / float(first[category]) * 100, 1)
    # 성장률이 큰 순서로 정렬합니다.
    ranked = sorted(growth.items(), key=lambda item: item[1], reverse=True)
    # 계산 결과가 비어 있으면 이후 1위 접근을 하지 않습니다.
    if not ranked:
        print("[안내] 성장률을 계산할 수 있는 카테고리가 없습니다.")
        return
    # 전체 카테고리 성장률을 콘솔에 출력합니다.
    print("[카테고리별 첫 달 대비 마지막 달 성장률]")
    for category, rate in ranked:
        print(f"  - {category}: {rate:+.1f}%")
    # 가장 높은 성장률과 가장 낮은 성장률을 출력합니다.
    print(f"\n[성장률 1위] {ranked[0][0]} ({ranked[0][1]:+.1f}%)")
    print(f"[성장률 최하위] {ranked[-1][0]} ({ranked[-1][1]:+.1f}%)")
    # 공통 최신 달 facts를 이용해 차트를 만듭니다.
    facts = load_facts()
    # 실습문제에서 요구한 고정 파일명으로 저장합니다.
    chart_path = make_category_chart(facts, filename="category_sales.png")
    # 저장된 차트 경로를 출력합니다.
    print(f"[차트 저장 완료] {chart_path}")


def _generate_for_month(month: str) -> Path | None:
    """특정 달 보고서를 만들고 예상 가능한 ValueError는 안내 메시지로 처리합니다."""
    try:
        # 지정한 월과 바로 이전 달로 facts를 계산합니다.
        facts = load_facts_for_month(month)
    except ValueError as error:
        # 없는 달 또는 첫 달 문제를 사용자에게 보여 주고 None을 반환합니다.
        print(f"[안내] {error}")
        return None
    # 선택한 OpenAI/Gemini 모델로 보고서를 만들고 API 실패 시 폴백을 사용합니다.
    body = write_report_with_fallback(facts)
    # 해당 월의 표준 월별 파일명으로 보고서를 저장합니다.
    return save_report(facts, body)


def exercise_2_specific_month_report() -> None:
    """실습 2: 존재하는 달과 존재하지 않는 달을 각각 지정해 예외 처리를 검증합니다."""
    # 데이터에서 첫 달 이후 사용 가능한 월 목록을 확인합니다.
    dataframe = pd.read_csv(DATA / "monthly_sales.csv", encoding="utf-8-sig").sort_values("month").reset_index(drop=True)
    # 전월 비교가 가능한 예시로 두 번째 이후 중 하나를 선택합니다.
    sample_month = str(dataframe.iloc[min(2, len(dataframe) - 1)]["month"])
    # 정상 동작 검증용 월을 출력합니다.
    print(f"[1] 존재하는 달: {sample_month}")
    # 정상 달 보고서 생성을 실행합니다.
    valid_path = _generate_for_month(sample_month)
    # 성공 여부와 저장 경로를 출력합니다.
    print("  결과:", f"저장됨 → {valid_path}" if valid_path else "생성 실패")

    # 존재하지 않는 달을 사용해 친절한 오류 메시지를 확인합니다.
    print("\n[2] 존재하지 않는 달: 1999-01")
    # 잘못된 월로 함수를 호출해 프로그램이 종료되지 않는지 확인합니다.
    invalid_path = _generate_for_month("1999-01")
    # None이 반환되면 예상된 실패임을 표시합니다.
    print("  결과:", f"저장됨 → {invalid_path}" if invalid_path else "생성 실패(예상된 동작)")
