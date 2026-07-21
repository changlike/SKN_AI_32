# Business Agent 콘솔 프로젝트

## 1. 프로젝트 개요

`data/monthly_sales.csv`의 숫자를 pandas로 정확히 계산하고, 
OpenAI 또는 Gemini가 확정된 수치만 근거로 경영진용 월간 매출 보고서를 작성하는 PyCharm 콘솔 앱입니다.

핵심 원칙은 다음과 같습니다.

```text
계산은 코드(pandas) → facts 확정
서술은 LLM          → facts로 보고서 작성
저장과 차트는 코드  → Markdown + PNG 자동 생성
```

HTML 문서와 references 폴더는 포함하지 않았고, HTML 설명을 출력하는 메뉴도 만들지 않았습니다.

## 2. 프로젝트 구조

```text
business_agent_console_project/
├── main.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── code/
│   ├── common.py
│   ├── app_context.py
│   ├── message_utils.py
│   ├── data_inspector.py
│   ├── business_service.py
│   ├── chart_service.py
│   └── exercises.py
├── data/
│   └── data.zip에서 추출한 전체 데이터
└── reports/
```

## 3. PyCharm 실행 방법

1. ZIP 파일을 원하는 폴더에 압축 해제합니다.
2. PyCharm에서 `business_agent_console_project` 폴더를 엽니다.
3. Python 3.10 이상 가상환경을 만듭니다.
4. PyCharm Terminal에서 패키지를 설치합니다.

```bash
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

5. `.env.example`을 복사해 `.env`를 만들고 API 키를 입력합니다.

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Windows 명령 프롬프트:

```cmd
copy .env.example .env
```

6. `main.py`를 실행합니다.

```bash
python main.py
```

## 4. 실행 메뉴

```text
1. data.zip 데이터 파일과 monthly_sales.csv 확인
2. pandas로 최신 달 핵심 수치 facts 집계
3. 안전 집계: 파일·컬럼·누락 데이터 예외 처리
4. OpenAI/Gemini로 경영진용 월간 보고서 서술
5. 집계 → 서술 → 월별 마크다운 리포트 저장
6. 카테고리별 매출 차트 PNG 생성
7. 차트를 포함한 마크다운 보고서 생성
8-1. 실습문제 해답 1: 카테고리 성장률 분석 + 차트
8-2. 실습문제 해답 2: 특정 달 지정 리포트 + 예외 처리
9. OpenAI / Gemini 공급자 다시 선택
0. 종료
```

## 5. 생성 파일

메뉴 5, 6, 7과 실습문제 메뉴를 실행하면 `reports/` 폴더에 다음 파일이 생성됩니다.

```text
monthly_sales_YYYY-MM.md
chart_YYYY-MM.png
monthly_sales_YYYY-MM_with_chart.md
category_sales.png
```

## 6. API 호출 실패 대응

API 키 누락, 네트워크 오류, 할당량 초과가 발생하면 보고서 메뉴는 확정 facts를 사용하는 코드 기반 기본 보고서로 대체합니다. 수치 계산은 항상 pandas가 담당하므로 LLM 실패가 숫자 정확성에 영향을 주지 않습니다.
