"""OpenAI 임베딩/LLM과 ChromaDB를 연결하는 RAG 핵심 서비스입니다."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import chromadb
from django.conf import settings
from openai import OpenAI

from boards.models import Board
from .document_loader import load_pdf_chunks, sha256_text


@dataclass
class SearchResult:
    """화면과 API에 전달할 벡터 검색 결과입니다."""

    text: str
    metadata: dict
    distance: float | None

    @property
    def similarity(self) -> float | None:
        """Chroma cosine distance를 사람이 보기 쉬운 유사도로 변환합니다."""
        if self.distance is None:
            return None
        return max(-1.0, min(1.0, 1.0 - float(self.distance)))


class RagService:
    """문서/게시글 색인, 벡터 검색, 근거 기반 답변 생성을 담당합니다."""

    COLLECTION_NAME = "django_docs_and_boards"

    def __init__(self):
        api_key = settings.OPENAI_API_KEY
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY가 설정되지 않았습니다. .env 파일을 확인하십시오.")

        self.openai = OpenAI(api_key=api_key)
        self.embedding_model = settings.OPENAI_EMBEDDING_MODEL
        self.chat_model = settings.OPENAI_CHAT_MODEL
        self.docs_dir = Path(settings.RAG_DOCS_DIR)
        self.vector_dir = Path(settings.RAG_VECTOR_DB_DIR)
        self.vector_dir.mkdir(parents=True, exist_ok=True)

        self.chroma = chromadb.PersistentClient(path=str(self.vector_dir))
        self.collection = self.chroma.get_or_create_collection(
            name=self.COLLECTION_NAME,
            # 최신 Chroma 설정 형식으로 HNSW 거리 함수를 cosine으로 지정합니다.
            configuration={"hnsw": {"space": "cosine"}},
        )

    def _embed(self, texts: list[str]) -> list[list[float]]:
        """OpenAI Embeddings API로 여러 텍스트를 벡터로 변환합니다."""
        if not texts:
            return []
        response = self.openai.embeddings.create(
            model=self.embedding_model,
            input=texts,
        )
        ordered = sorted(response.data, key=lambda item: item.index)
        return [item.embedding for item in ordered]

    def _batched(self, items: list, size: int = 64) -> Iterable[list]:
        """API 한 번에 너무 많은 텍스트를 보내지 않도록 배치로 나눕니다."""
        for i in range(0, len(items), size):
            yield items[i : i + size]

    def _stored_hashes(self, source_type: str) -> dict[str, set[str]]:
        """벡터DB에 저장된 source_key별 content_hash 집합을 읽습니다."""
        data = self.collection.get(
            where={"source_type": source_type},
            include=["metadatas"],
        )
        result: dict[str, set[str]] = {}
        for metadata in data.get("metadatas") or []:
            if not metadata:
                continue
            source_key = str(metadata.get("source_key", ""))
            content_hash = str(metadata.get("content_hash", ""))
            result.setdefault(source_key, set()).add(content_hash)
        return result

    def sync_documents(self, force: bool = False) -> dict:
        """docs 폴더 PDF를 읽어 변경된 문서만 ChromaDB에 재색인합니다."""
        self.docs_dir.mkdir(parents=True, exist_ok=True)
        stored = self._stored_hashes("document")
        current_source_keys: set[str] = set()
        indexed_files = 0
        indexed_chunks = 0
        skipped_files = 0

        for pdf_path in sorted(self.docs_dir.glob("*.pdf")):
            chunks = load_pdf_chunks(pdf_path)
            if not chunks:
                continue
            source_key = chunks[0].metadata["source_key"]
            current_source_keys.add(source_key)
            current_hashes = {c.metadata["content_hash"] for c in chunks}

            if not force and stored.get(source_key) == current_hashes:
                skipped_files += 1
                continue

            self.collection.delete(where={"source_key": source_key})
            for batch in self._batched(chunks):
                texts = [c.text for c in batch]
                embeddings = self._embed(texts)
                self.collection.upsert(
                    ids=[c.chunk_id for c in batch],
                    documents=texts,
                    metadatas=[c.metadata for c in batch],
                    embeddings=embeddings,
                )
                indexed_chunks += len(batch)
            indexed_files += 1

        for old_source_key in set(stored) - current_source_keys:
            self.collection.delete(where={"source_key": old_source_key})

        return {
            "indexed_files": indexed_files,
            "indexed_chunks": indexed_chunks,
            "skipped_files": skipped_files,
        }

    def _board_payload(self, board: Board) -> tuple[str, dict]:
        """게시글 하나를 검색 가능한 텍스트와 메타데이터로 변환합니다."""
        text = (
            f"게시글 번호: {board.pk}\n"
            f"제목: {board.title}\n"
            f"작성자: {board.author.display_name}\n"
            f"작성일: {board.created_at:%Y-%m-%d %H:%M}\n"
            f"내용: {board.content}"
        )
        source_key = f"board:{board.pk}"
        metadata = {
            "source_type": "board",
            "source_key": source_key,
            "board_id": int(board.pk),
            "title": board.title,
            "author": board.author.display_name,
            "content_hash": sha256_text(text),
        }
        return text, metadata

    def sync_boards(self, force: bool = False) -> dict:
        """Django 게시글을 ChromaDB와 증분 동기화합니다."""
        stored = self._stored_hashes("board")
        current_source_keys: set[str] = set()
        indexed = 0
        skipped = 0

        boards = Board.objects.select_related("author").all()
        for board in boards:
            text, metadata = self._board_payload(board)
            source_key = metadata["source_key"]
            current_source_keys.add(source_key)
            current_hash = metadata["content_hash"]

            if not force and stored.get(source_key) == {current_hash}:
                skipped += 1
                continue

            embedding = self._embed([text])[0]
            vector_id = "board-" + hashlib.sha256(source_key.encode("utf-8")).hexdigest()[:24]
            self.collection.delete(where={"source_key": source_key})
            self.collection.upsert(
                ids=[vector_id],
                documents=[text],
                metadatas=[metadata],
                embeddings=[embedding],
            )
            indexed += 1

        for old_source_key in set(stored) - current_source_keys:
            self.collection.delete(where={"source_key": old_source_key})

        return {"indexed": indexed, "skipped": skipped}

    def sync_all(self, force: bool = False) -> dict:
        """PDF 문서와 게시글을 모두 벡터DB에 동기화합니다."""
        return {
            "documents": self.sync_documents(force=force),
            "boards": self.sync_boards(force=force),
        }

    def search(self, question: str, source_scope: str = "all", top_k: int = 5) -> list[SearchResult]:
        """질문 임베딩과 가장 가까운 문서/게시글 청크를 검색합니다."""
        query_embedding = self._embed([question])[0]
        where = None
        if source_scope == "documents":
            where = {"source_type": "document"}
        elif source_scope == "boards":
            where = {"source_type": "board"}

        kwargs = {
            "query_embeddings": [query_embedding],
            "n_results": max(1, min(top_k, 10)),
            "include": ["documents", "metadatas", "distances"],
        }
        if where:
            kwargs["where"] = where

        data = self.collection.query(**kwargs)
        docs = (data.get("documents") or [[]])[0]
        metadatas = (data.get("metadatas") or [[]])[0]
        distances = (data.get("distances") or [[]])[0]

        return [
            SearchResult(text=text, metadata=metadata or {}, distance=distance)
            for text, metadata, distance in zip(docs, metadatas, distances)
        ]

    def answer(self, question: str, results: list[SearchResult]) -> str:
        """검색 결과만 근거로 사용하도록 LLM 프롬프트를 구성하여 답변합니다."""
        if not results:
            return "검색된 근거가 없어 답변할 수 없습니다."

        context_blocks = []
        for index, result in enumerate(results, start=1):
            metadata = result.metadata
            if metadata.get("source_type") == "document":
                source_label = f"문서: {metadata.get('title')} / {metadata.get('page')}쪽"
            else:
                source_label = f"게시글 #{metadata.get('board_id')}: {metadata.get('title')}"
            context_blocks.append(f"[근거 {index}] {source_label}\n{result.text}")

        context = "\n\n".join(context_blocks)
        instructions = (
            "당신은 Django 수업 프로젝트의 RAG 답변 도우미입니다. "
            "반드시 제공된 검색 근거 안에서만 답하십시오. "
            "근거에 없는 사실은 추측하지 말고 '제공된 근거에서 확인되지 않습니다'라고 말하십시오. "
            "답변은 자연스러운 한국어로 작성하고, 중요한 주장 뒤에는 [근거 1]처럼 근거 번호를 표시하십시오."
        )
        user_input = f"질문:\n{question}\n\n검색 근거:\n{context}"

        response = self.openai.responses.create(
            model=self.chat_model,
            instructions=instructions,
            input=user_input,
        )
        return response.output_text.strip()
