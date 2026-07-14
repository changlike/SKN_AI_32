"""
Tool, Resource, Prompt를 등록해서 제공하는 독립 MCP 서버임
"""

# MCP 서버 객체 생성용
from mcp.server.fastmcp import FastMCP

# Resource 등록을 위해 리소스 가져옴
from mcp_server.resources import document_catalog, runtime_config

# Tool 등록을 위해 툴 가져옴
from mcp_server.tools import (
    add_numbers,
    ask_rag,
    list_files,
    list_mysql_knowledge,
    read_file,
    rebuild_index,
    search_documents,
)

# 서버 객체 생성 =================================
mcp = FastMCP("MCP RAG Assistant")

# Tool 등록 ======================================
# 별도로 작성해서 임포트한 함수를 Tool로 등록하는 방법

# 계산 Tool를 MCP에 등록함
@mcp.tool()
def add(a:float, b:float) -> float:
    """두 숫자를 더합니다."""

    # 준비된 함수에 처리를 위임(weaving)함
    return add_numbers(a,b)

@mcp.tool()
def list_document_files() -> list[str]:
    """등록된 문서 파일 목록을 조회합니다."""
    # 파라미터 없음: 조회 대상이 고정된 디렉터리/DB이므로 인자 불필요
    return list_files()

@mcp.tool()
def read_document_file(file_name: str) -> str:
    """지정한 문서 파일의 내용을 읽어옵니다."""
    return read_file(file_name)

@mcp.tool()
def vector_search(query: str, top_k: int = 5) -> list[dict]:
    """쿼리와 유사한 문서 청크를 벡터 검색합니다."""
    return search_documents(query, top_k)

@mcp.tool()
def rebuild_rag_index() -> dict:
    """RAG 인덱스를 처음부터 다시 빌드합니다."""
    # 콜론 누락(SyntaxError) 수정됨: -> bool:
    return rebuild_index()

@mcp.tool()
def rag_question_answer(question: str) -> dict:

    """RAG 파이프라인으로 질문에 답합니다."""
    return ask_rag(question)

@mcp.tool()
def mysql_knowledge_list() -> list[dict]:
    """ MySQL 지식 목록을 조회합니다. """

    # 공통 MySQL Tool을 호출합니다.
    return list_mysql_knowledge()

# 별도로 작성해서 임포트한 리소스 등록 ======================

# 현재 실행 설정 Resource 등록
@mcp.resource("config://runtime")
def config_resource() -> str:
    """민감 정보 제외한 앱의 실행 설정을 제공합니다. """

    # Resource 구현 함수를 호출함
    return runtime_config()

# 문서 카탈로그 Resource 등록
@mcp.resource("docs://catalog")
def docs_resource() -> str: # 등록 함수명과 구현 함수명의 이름 달라도 됨
    """docs 폴더의 파일 목록을 제공합니다."""

    # Resource 구현 함수를 호출함
    return document_catalog()

# RAG 질문용 Prompt를 등록합니다.
@mcp.prompt()
def grounded_rag_prompt(question: str) -> str:
    """검색 근거만 사용하도록 지시하는 RAG Prompt를 반환합니다."""

    # MCP Client가 활용할 재사용 Prompt 문자열을 반환합니다.
    return (
        "먼저 vector_search 또는 rag_question_answer Tool을 사용하세요.\n"
        "검색 결과에 포함된 문서만 근거로 답하세요.\n"
        "확인할 수 없는 내용은 추측하지 마세요.\n\n"
        f"사용자 질문: {question}"
    )

# 서버 파일을 직접 실행했을 때 stdio 전송 방식으로 MCP 서버를 시작합니다.
if __name__ == "__main__":
    # MCP Client와 표준 입력•출력으로 통신하도록 서버를 실행합니다.
    mcp.run(transport="stdio")
















