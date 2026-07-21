# -*- coding: utf-8 -*-
"""data.zip에서 제공된 데이터 파일과 monthly_sales.csv를 확인하는 기능입니다."""

from pathlib import Path
import pandas as pd
from common import DATA


def list_data_files() -> list[Path]:
    """data 폴더 아래의 모든 파일을 상대경로 기준으로 정렬해 반환합니다."""
    # DATA가 없을 경우 빈 목록을 반환하여 콘솔 앱이 예외로 종료되지 않게 합니다.
    if not DATA.exists():
        return []
    # 폴더를 제외한 실제 파일만 찾고, 표시가 일정하도록 문자열 경로로 정렬합니다.
    return sorted((path for path in DATA.rglob("*") if path.is_file()), key=lambda p: str(p))


def print_data_summary() -> None:
    """data 파일 목록과 월간 매출 데이터의 구조를 콘솔에 출력합니다."""
    # 데이터 폴더의 절대경로를 먼저 보여 줍니다.
    print(f"[데이터 폴더] {DATA}")
    # 재사용 가능한 함수로 전체 파일 목록을 가져옵니다.
    files = list_data_files()
    # 데이터 파일이 없으면 안내 후 함수를 종료합니다.
    if not files:
        print("[안내] data 폴더에 파일이 없습니다.")
        return
    # 파일 수를 출력합니다.
    print(f"[전체 파일 수] {len(files)}개")
    # 각 파일의 상대경로와 바이트 크기를 출력합니다.
    for index, path in enumerate(files, start=1):
        print(f"  {index:02d}. {path.relative_to(DATA)} ({path.stat().st_size:,} bytes)")

    # 제24강 핵심 데이터의 경로를 구성합니다.
    sales_path = DATA / "monthly_sales.csv"
    # 핵심 CSV가 존재하지 않으면 이후 pandas 읽기를 하지 않습니다.
    if not sales_path.exists():
        print("\n[안내] monthly_sales.csv 파일을 찾지 못했습니다.")
        return
    # UTF-8 BOM까지 안전하게 처리하도록 utf-8-sig로 읽습니다.
    dataframe = pd.read_csv(sales_path, encoding="utf-8-sig")
    # 데이터 크기와 컬럼을 확인합니다.
    print(f"\n[monthly_sales.csv] 행={len(dataframe)}, 열={len(dataframe.columns)}")
    print("[컬럼]", list(dataframe.columns))
    # 전체 행이 많아도 콘솔이 길어지지 않도록 앞쪽 5행만 출력합니다.
    print("[앞 5행]")
    print(dataframe.head().to_string(index=False))
