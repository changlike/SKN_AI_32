"""
간단 MCP (Model Context Protocol) 서버 예제

구현 내용:
1. FastMCP 서버 객체 생성
2. TOOL 등록
3. RESOURCE 등록
4. PROMPT 등록
5. MCP 서버 실행 (stdio 방식)
"""

# 파이썬 버전의 타입 힌트 평가 방식을 사용하도록 설정
from __future__ import annotations

# 현재 날짜와 시간을 생성하기 위해 datetime 클래스 가져옴
from datetime import datetime

# 파일과 디렉토리 경로를 운영체제와 관계없이 처리하기 위해 Path 클래스 가져옴
from pathlib import Path

# MCP Python SDK에서 간단한 서버 만들 수 있는 FastMCP 클래스 가져옴
from mcp.server.fastmcp import FastMCP


# 전역 변수 선언 (프로그램 실행 시 메모리에 딱 한번 기록하기 위함) --------------- => singleton 개념

# 현재 server.py 파일이 저장된 프로젝트 루트 디렉토리 경로를 구함
BASE_DIR = Path(__file__).resolve().parent

# Resource에서 읽어서 반환할 예제 문서 파일의 전체 경로를 생성함
MANUAL_FILE = BASE_DIR / "data" / "manual.txt"

# MCP 서버 객체 생성함
mcp = FastMCP("Simple MCP Server")

# TOOL 등록 *****************************************
# 함수를 MCP Tool로 등록함
@mcp.tool()
def hello(name: str) -> str:
    """
    이름을 전달받아서 인사말을 만들어서 반환합니다.
    Args:
        name: 인사말에 포함할 사용자 이름입니다.

    Returns:
        사용자 이름이 포함된 인사말 문자열입니다.
    """
    return f"안녕하세요. {name}님! MCP Tool 호출에 성공하셨습니다."
# def hello() --------------------------------------

@mcp.tool()
def add(a:int, b:int) -> int:
    """
    숫자 2개를 전달받아서 더하기 한 결과를 반환합니다.
    Args:
        a: 첫번째 숫자입니다.
        b: 두번째 숫자입니다.

    Returns:
        a와 b를 더한 숫자입니다.
    """
    return a + b
# def add() ------------------------------------------------

@mcp.tool()
def get_current_time() -> str:
    """
    MCP 서버가 실행 중인 컴퓨터의 현재 날짜와 시간을 반환합니다.
    Return:
          YYYY-MM-DD HH:MM:SS 형식의 문자열입니다.
    """
    # 서버 컴퓨터의 현재 날짜와 시간을 구함
    current_time = datetime.now()

    # 현재 날짜와 시간 정보를 읽기 쉬운 문자열로 바꾸고 반환함
    return current_time.strftime("%Y-%m-%d %H:%M:%S")
# def get_current_time() -------------------------------------------------

# RESOURCE 등록 ****************************************
# manual://guide URL로 접근할 수 있는 RESOURCE로 등록함
@mcp.resource("manual://guide")
def read_manual() -> str:
    """
    data/manual.txt 파일의 내용을 읽어서 MCP Resource로 제공합니다.
    Returns:
        사용설명서 파일의 전체 내용 문자열입니다.
    """
    # 메뉴얼 문서 파일이 존재하지 않으면, 오류 메세지를 반환함
    if not MANUAL_FILE.exists():
        return "manual.txt 파일을 찾을 수 없습니다."

    # utf-8 인코딩으로 문서 전체를 읽어서 반환함
    return  MANUAL_FILE.read_text(encoding="utf-8")
# def read_manual() --------------------------------------------

# URI의 이름 부분을 변수로 전달받는 동적 Resource로 등록함
@mcp.resource("profile://{name}")
def get_profile(name: str) -> str:
    """
    URL에 포함된 이름으로 간단 사용자 프로필을 생성합니다.
    Args:
        name: profile://URL에 포함된 사용자 이름입니다.

    Returns:
        이름이 포함된 간단 프로필 문자열입니다.
    """
    return (
        f"사용자 이름: {name}\n"
        "학습 주제: MCP Server\n"
        "현재 단계: Tool, Resource, Prompt 등록 실습"
            )
# def_get_profile(name: str) --------------------------------------

# PROMPT 등록 ***********************************
# 재사용 가능한 Prompt를 등록함
@mcp.prompt()
def summarize_document(topic: str, style: str = "쉽게") -> str:
    """
    특정 주제(topic)를 요약하도록 LLM에 전달할 Prompt를 생성합니다.
    Args:
        topic: 요약할 주제입니다.
        style: 요약 문체입니다. ("짧게", "간단하게")

    Return:
        LLM에 전달할 최종 Prompt 문자열입니다.
    """
    return (
        f"다음 주제를 {style} 설명하세요."
        "핵심 개념, 동작 과정, 간단한 예제를 포함하세요.\n\n"
        f"주제: {topic}"
    )
# def -----------------------------------

# 서버 실행
if __name__ == "__main__":
    # stdio 전송 방식으로 MCP 서버를 실행함
    # MCP Client는 이 프로세스(실행 중인 프로그램)의 표준 입력(키보드)과 표준 출력(화면출력)을 이용해서 통신할 것임
    mcp.run(transport="stdio")











