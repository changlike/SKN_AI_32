"""docs 폴더의 PDF를 읽고 RAG용 청크로 분할합니다."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from pypdf import PdfReader


@dataclass
class TextChunk:
    """벡터DB에 저장할 하나의 텍스트 청크와 메타데이터입니다."""

    chunk_id: str
    text: str
    metadata: dict


def sha256_text(text: str) -> str:
    """텍스트 변경 여부 확인에 사용할 SHA-256 해시를 반환합니다."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def split_text(text: str, chunk_size: int = 1000, overlap: int = 150) -> list[str]:
    """문자 단위로 텍스트를 겹치게 분할하여 문맥 단절을 줄입니다."""
    normalized = " ".join(text.split())
    if not normalized:
        return []

    chunks: list[str] = []
    start = 0
    while start < len(normalized):
        end = min(start + chunk_size, len(normalized))
        chunks.append(normalized[start:end])
        if end >= len(normalized):
            break
        start = max(end - overlap, start + 1)
    return chunks


def load_pdf_chunks(pdf_path: Path) -> list[TextChunk]:
    """PDF 각 페이지의 텍스트를 추출하고 페이지별 청크를 생성합니다."""
    reader = PdfReader(str(pdf_path))
    title = ((reader.metadata.title if reader.metadata else None) or pdf_path.stem).strip()
    source_key = f"document:{pdf_path.name}"
    chunks: list[TextChunk] = []

    for page_number, page in enumerate(reader.pages, start=1):
        page_text = page.extract_text() or ""
        for chunk_index, chunk_text in enumerate(split_text(page_text)):
            content_hash = sha256_text(chunk_text)
            chunk_id = sha256_text(
                f"{source_key}:{page_number}:{chunk_index}"
            )[:32]
            chunks.append(
                TextChunk(
                    chunk_id=f"doc-{chunk_id}",
                    text=chunk_text,
                    metadata={
                        "source_type": "document",
                        "source_key": source_key,
                        "title": title,
                        "filename": pdf_path.name,
                        "page": page_number,
                        "chunk_index": chunk_index,
                        "content_hash": content_hash,
                    },
                )
            )
    return chunks
