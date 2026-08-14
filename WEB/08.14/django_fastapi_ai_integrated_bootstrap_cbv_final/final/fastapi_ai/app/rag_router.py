"""Django가 호출하는 FastAPI RAG REST API 엔드포인트를 정의합니다."""
# FastAPI 라우터와 HTTP 오류 클래스를 가져옵니다.
from fastapi import APIRouter, HTTPException, Query
# PDF 원문 파일을 스트리밍하기 위해 FileResponse를 가져옵니다.
from fastapi.responses import FileResponse
# 경로 조작 공격을 막기 위한 안전한 경로 비교에 Path를 사용합니다.
from pathlib import Path
# 요청 JSON 검증을 위한 Pydantic BaseModel과 Field를 가져옵니다.
from pydantic import BaseModel, Field
# RAG 핵심 서비스 클래스를 가져옵니다.
from app.services.rag_service import RagService
# 실제 근거 PDF가 저장된 디렉터리 경로를 가져옵니다.
from app.config import DOCS_DIR

# /api/rag 공통 경로를 사용하는 라우터를 생성합니다.
router = APIRouter(prefix="/api/rag", tags=["RAG"])


class RagQueryRequest(BaseModel):
    """Django가 FastAPI로 전송하는 RAG 질문 JSON 구조입니다."""
    # 실제 자연어 질문이며 빈 문자열을 막습니다.
    question: str = Field(min_length=1, max_length=1000)
    # all, documents, boards 중 하나의 검색 범위를 받습니다.
    source_scope: str = Field(default="all")
    # 반환할 유사 문서 개수를 1~10 사이로 제한합니다.
    top_k: int = Field(default=5, ge=1, le=10)
    # 질문 전에 변경된 문서/게시글을 자동 동기화할지 지정합니다.
    sync_before_search: bool = Field(default=True)


def _serialize_result(result) -> dict:
    """SearchResult 객체를 JSON 직렬화 가능한 dict로 변환합니다."""
    # Django 템플릿에서 바로 쓸 수 있도록 텍스트, 유사도, 메타데이터를 구조화합니다.
    return {"text": result.text, "similarity": result.similarity, "metadata": result.metadata}


@router.post("/query")
def rag_query(payload: RagQueryRequest) -> dict:
    """문서/게시글을 검색하고 OpenAI가 근거 기반 최종 답변을 생성합니다."""
    # 허용되지 않은 검색 범위는 명확한 422 오류로 거부합니다.
    if payload.source_scope not in {"all", "documents", "boards"}:
        raise HTTPException(status_code=422, detail="source_scope는 all, documents, boards 중 하나여야 합니다.")
    try:
        # 요청 단위 RAG 서비스 객체를 생성합니다.
        service = RagService()
        # 기본 동작에서는 변경된 PDF와 게시글을 먼저 증분 동기화합니다.
        sync_result = service.sync_all(force=False) if payload.sync_before_search else None
        # 질문과 의미상 가까운 근거를 벡터DB에서 검색합니다.
        results = service.search(payload.question, payload.source_scope, payload.top_k)
        # 검색된 근거만 사용하여 LLM 최종 답변을 생성합니다.
        answer = service.answer(payload.question, results)
        # Django가 그대로 사용할 수 있는 JSON 응답을 반환합니다.
        return {"success": True, "question": payload.question, "answer": answer, "sync_result": sync_result, "results": [_serialize_result(item) for item in results]}
    except Exception as exc:
        # DB, OpenAI, ChromaDB 오류를 FastAPI 500 응답으로 변환합니다.
        raise HTTPException(status_code=500, detail=f"RAG 처리 실패: {exc}") from exc


@router.post("/reindex")
def rag_reindex(force: bool = Query(default=True)) -> dict:
    """관리 또는 수업 실습용으로 전체 RAG 색인을 다시 생성합니다."""
    try:
        # RAG 서비스를 생성합니다.
        service = RagService()
        # force=True이면 기존 해시와 관계없이 모든 근거를 다시 임베딩합니다.
        result = service.sync_all(force=force)
        # 처리 통계를 JSON으로 반환합니다.
        return {"success": True, "force": force, "result": result}
    except Exception as exc:
        # 색인 오류의 실제 원인을 detail에 포함합니다.
        raise HTTPException(status_code=500, detail=f"RAG 재색인 실패: {exc}") from exc


@router.get("/documents/{filename}")
def rag_document(filename: str) -> FileResponse:
    """Django 화면에서 선택한 RAG 근거 PDF 원문을 안전하게 제공합니다."""
    # docs 디렉터리의 절대 경로를 계산합니다.
    docs_root = Path(DOCS_DIR).resolve()
    # 사용자 입력 파일명을 docs 아래 경로로 결합한 뒤 절대 경로로 정규화합니다.
    target = (docs_root / filename).resolve()
    # 상위 경로 탈출, 존재하지 않는 파일, PDF가 아닌 파일 요청을 모두 차단합니다.
    if docs_root not in target.parents or not target.is_file() or target.suffix.lower() != ".pdf":
        raise HTTPException(status_code=404, detail="근거 PDF를 찾을 수 없습니다.")
    # 브라우저가 PDF로 인식할 수 있도록 media_type을 명시해 파일을 반환합니다.
    return FileResponse(path=str(target), media_type="application/pdf")
