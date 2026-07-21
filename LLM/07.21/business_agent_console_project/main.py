# -*- coding: utf-8 -*-
"""제24강 Business Agent를 PyCharm에서 실행하는 메인 콘솔 프로그램입니다."""

import sys
from pathlib import Path

# code 폴더의 모듈을 import할 수 있도록 프로젝트 내부 경로를 추가합니다.
PROJECT_ROOT = Path(__file__).resolve().parent
# 공통 모듈과 서비스 모듈이 있는 code 폴더 경로를 계산합니다.
CODE_DIR = PROJECT_ROOT / "code"
# 같은 경로가 중복되지 않을 때만 Python 모듈 검색 경로 앞에 추가합니다.
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from app_context import get_provider_label, set_provider
from business_service import (
    format_facts,
    generate_monthly_report,
    load_facts,
    load_facts_safe,
    save_report,
    write_report_with_fallback,
)
from chart_service import add_chart_to_report, make_category_chart
from data_inspector import print_data_summary
from exercises import exercise_1_category_growth_and_chart, exercise_2_specific_month_report


def select_provider() -> None:
    """OpenAI와 Gemini 중 현재 실행에 사용할 모델 공급자를 선택합니다."""
    # 사용자가 올바른 값을 선택할 때까지 메뉴를 반복합니다.
    while True:
        print("\n" + "=" * 72)
        print("LLM 공급자 선택")
        print("1. OpenAI")
        print("2. Google Gemini")
        print("0. 프로그램 종료")
        print("=" * 72)
        # 콘솔 입력의 앞뒤 공백을 제거합니다.
        choice = input("선택: ").strip()
        # 1번은 OpenAI 공급자를 전역 상태에 저장합니다.
        if choice == "1":
            set_provider("openai")
            print("[선택 완료] OpenAI")
            return
        # 2번은 Gemini 공급자를 전역 상태에 저장합니다.
        if choice == "2":
            set_provider("gemini")
            print("[선택 완료] Google Gemini")
            return
        # 0번은 정상 종료 코드를 사용해 프로그램을 끝냅니다.
        if choice == "0":
            raise SystemExit(0)
        # 그 외 입력은 오류 메시지를 보여 주고 메뉴를 다시 표시합니다.
        print("[입력 오류] 0, 1, 2 중 하나를 입력하세요.")


def print_menu() -> None:
    """HTML 요약 메뉴를 제외한 중요 실행 코드 메뉴만 출력합니다."""
    print("\n" + "=" * 72)
    print(f"제24강 Business Agent 콘솔 앱 | 현재 모델: {get_provider_label()}")
    print("=" * 72)
    print("1. data.zip 데이터 파일과 monthly_sales.csv 확인")
    print("2. pandas로 최신 달 핵심 수치 facts 집계")
    print("3. 안전 집계: 파일·컬럼·누락 데이터 예외 처리")
    print("4. OpenAI/Gemini로 경영진용 월간 보고서 서술")
    print("5. 집계 → 서술 → 월별 마크다운 리포트 저장")
    print("6. 카테고리별 매출 차트 PNG 생성")
    print("7. 차트를 포함한 마크다운 보고서 생성")
    print("8-1. 실습문제 해답 1: 카테고리 성장률 분석 + 차트")
    print("8-2. 실습문제 해답 2: 특정 달 지정 리포트 + 예외 처리")
    print("9. OpenAI / Gemini 공급자 다시 선택")
    print("0. 종료")
    print("=" * 72)


def run_menu(choice: str) -> bool:
    """선택한 메뉴 기능을 실행하고 계속 실행 여부를 반환합니다."""
    # 1번은 data.zip에서 추출한 파일과 핵심 CSV 내용을 확인합니다.
    if choice == "1":
        print_data_summary()
    # 2번은 LLM 없이 pandas 계산 결과만 확인합니다.
    elif choice == "2":
        facts = load_facts()
        print("[코드로 확정한 facts]")
        print(format_facts(facts))
    # 3번은 오류를 던지지 않는 안전 집계 결과 구조를 확인합니다.
    elif choice == "3":
        safe_facts = load_facts_safe()
        print("[안전 집계 결과]")
        print(safe_facts)
    # 4번은 현재 선택된 OpenAI/Gemini로 보고서를 작성합니다.
    elif choice == "4":
        facts = load_facts()
        print("[LLM 보고서 생성 중]")
        print(write_report_with_fallback(facts))
    # 5번은 최신 달 전체 파이프라인을 실행해 md 파일을 저장합니다.
    elif choice == "5":
        path = generate_monthly_report()
        print(f"[리포트 저장 완료] {path}")
    # 6번은 최신 달 카테고리별 PNG 차트를 만듭니다.
    elif choice == "6":
        facts = load_facts()
        path = make_category_chart(facts)
        print(f"[차트 저장 완료] {path}")
    # 7번은 LLM 본문 앞에 차트 링크를 삽입한 보고서를 저장합니다.
    elif choice == "7":
        facts = load_facts()
        chart_path = make_category_chart(facts)
        body = write_report_with_fallback(facts)
        body_with_chart = add_chart_to_report(body, chart_path)
        report_path = save_report(facts, body_with_chart, filename=f"monthly_sales_{facts['month']}_with_chart.md")
        print(f"[차트 저장 완료] {chart_path}")
        print(f"[차트 포함 보고서 저장 완료] {report_path}")
    # 8-1번은 실습문제 1의 완성 해답을 실행합니다.
    elif choice == "8-1":
        exercise_1_category_growth_and_chart()
    # 8-2번은 실습문제 2의 완성 해답을 실행합니다.
    elif choice == "8-2":
        exercise_2_specific_month_report()
    # 9번은 실행 중에도 모델 공급자를 바꿀 수 있게 합니다.
    elif choice == "9":
        select_provider()
    # 0번은 메인 반복문 종료를 요청합니다.
    elif choice == "0":
        return False
    # 등록되지 않은 메뉴 입력은 안내만 하고 앱을 계속 실행합니다.
    else:
        print("[입력 오류] 메뉴에 표시된 값을 입력하세요.")
    # 0번이 아니면 계속 실행합니다.
    return True


def main() -> None:
    """공급자를 선택한 뒤 사용자가 종료할 때까지 메뉴를 반복합니다."""
    # 프로그램 시작 시 사용할 LLM 공급자를 먼저 선택합니다.
    select_provider()
    # 메뉴 반복 여부를 저장합니다.
    running = True
    # 0번을 선택하기 전까지 콘솔 메뉴를 반복합니다.
    while running:
        # 현재 가능한 중요 코드 메뉴를 출력합니다.
        print_menu()
        # 사용자 입력을 문자열로 받습니다.
        choice = input("메뉴 선택: ").strip()
        try:
            # 선택 메뉴를 실행하고 다음 반복 여부를 갱신합니다.
            running = run_menu(choice)
        except KeyboardInterrupt:
            # Ctrl+C가 입력되면 보기 좋은 메시지를 출력하고 종료합니다.
            print("\n[중단] 사용자가 실행을 중단했습니다.")
            break
        except Exception as error:
            # 개별 메뉴 오류로 전체 앱이 종료되지 않도록 오류 유형과 내용을 출력합니다.
            print(f"[실행 오류] {type(error).__name__}: {error}")
    # 정상 종료 메시지를 출력합니다.
    print("프로그램을 종료합니다.")


# 이 파일을 직접 실행했을 때만 main 함수를 호출합니다.
if __name__ == "__main__":
    main()
