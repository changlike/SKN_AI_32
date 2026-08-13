"""PDF 근거 문서를 읽고 RAG 벡터 색인 단위로 분할합니다."""
# 향후 타입 힌트 평가를 지연하여 파이썬 버전 호환성을 높입니다.
from __future__ import annotations
# 청크 ID와 변경 감지 해시 생성을 위해 hashlib를 가져옵니다.
import hashlib
# 청크 데이터 구조 정의를 위해 dataclass를 가져옵니다.
from dataclasses import dataclass
# 파일 경로 처리를 위해 Path를 가져옵니다.
from pathlib import Path
# PDF 텍스트 추출을 위해 PdfReader를 가져옵니다.
from pypdf import PdfReader
# RAG 청크 설정값을 가져옵니다.
from app.config import settings


@dataclass
class TextChunk:
    """ChromaDB에 저장할 텍스트와 메타데이터를 묶는 데이터 클래스입니다."""
    # ChromaDB에서 중복 없이 사용할 고유 청크 ID입니다.
    chunk_id: str
    # 임베딩하고 검색할 실제 텍스트입니다.
    text: str
    # 문서명, 페이지, 출처 유형 등의 검색 메타데이터입니다.
    metadata: dict


def sha256_text(text_value: str) -> str:
    """텍스트 변경 여부를 비교하기 위한 SHA-256 해시를 반환합니다."""
    # 문자열을 UTF-8 바이트로 바꾸고 안정적인 16진수 해시를 생성합니다.
    return hashlib.sha256(text_value.encode("utf-8")).hexdigest()


def split_text(text_value: str) -> list[str]:
    """긴 문장을 일정 크기로 겹쳐 잘라 검색 문맥 손실을 줄입니다."""
    # 연속 공백과 줄바꿈을 하나의 공백으로 정규화합니다.
    normalized = " ".join(text_value.split())
    # 추출할 텍스트가 없으면 빈 리스트를 반환합니다.
    if not normalized:
        return []
    # 최종 청크들을 저장할 리스트를 준비합니다.
    chunks: list[str] = []
    # 현재 청크의 시작 위치를 0으로 초기화합니다.
    start = 0
    # 전체 문자열 끝까지 반복합니다.
    while start < len(normalized):
        # 설정된 크기를 넘지 않도록 청크 끝 위치를 계산합니다.
        end = min(start + settings.rag_chunk_size, len(normalized))
        # 계산한 범위를 하나의 청크로 추가합니다.
        chunks.append(normalized[start:end])
        # 전체 끝에 도달하면 반복을 종료합니다.
        if end >= len(normalized):
            break
        # 이전 청크의 끝 일부를 다음 청크에 겹치게 하여 문맥 연결을 보존합니다.
        start = max(end - settings.rag_chunk_overlap, start + 1)
    # 완성한 청크 목록을 반환합니다.
    return chunks


def load_pdf_chunks(pdf_path: Path) -> list[TextChunk]:
    """PDF 페이지별 텍스트를 추출하고 ChromaDB용 청크를 생성합니다."""
    # 파일에서 PDF 구조와 페이지를 읽습니다.
    reader = PdfReader(str(pdf_path))
    # PDF 메타데이터 제목이 있으면 사용하고 없으면 파일명을 제목으로 사용합니다.
    title = ((reader.metadata.title if reader.metadata else None) or pdf_path.stem).strip()
    # 같은 파일을 식별할 논리적인 출처 키를 생성합니다.
    source_key = f"document:{pdf_path.name}"
    # 결과 청크 목록을 초기화합니다.
    chunks: list[TextChunk] = []
    # 페이지 번호를 사람이 읽는 1부터 시작하여 순회합니다.
    for page_number, page in enumerate(reader.pages, start=1):
        # 페이지 내 텍스트를 추출하며 텍스트가 없으면 빈 문자열을 사용합니다.
        page_text = page.extract_text() or ""
        # 페이지 텍스트를 설정된 크기로 나누어 순회합니다.
        for chunk_index, chunk_text in enumerate(split_text(page_text)):
            # 실제 내용이 바뀌었는지 확인할 해시를 생성합니다.
            content_hash = sha256_text(chunk_text)
            # 파일명, 페이지, 청크 순번 조합으로 재현 가능한 ID를 생성합니다.
            raw_id = sha256_text(f"{source_key}:{page_number}:{chunk_index}")[:32]
            # 하나의 RAG 청크 객체를 생성해 목록에 추가합니다.
            chunks.append(TextChunk(chunk_id=f"doc-{raw_id}", text=chunk_text, metadata={
                "source_type": "document",
                "source_key": source_key,
                "title": title,
                "filename": pdf_path.name,
                "page": page_number,
                "chunk_index": chunk_index,
                "content_hash": content_hash,
            }))
    # PDF에서 생성한 모든 청크를 반환합니다.
    return chunks
