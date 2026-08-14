"""OpenAI Embeddings + ChromaDB + MySQL 게시글을 결합하는 RAG 핵심 서비스입니다."""
# 타입 힌트의 지연 평가를 활성화합니다.
from __future__ import annotations
# 게시글 벡터 ID 생성을 위해 hashlib를 가져옵니다.
import hashlib
# 검색 결과 구조체 정의를 위해 dataclass를 가져옵니다.
from dataclasses import dataclass
# 여러 타입을 묶는 Iterable 타입 힌트를 가져옵니다.
from typing import Iterable
# ChromaDB 영구 벡터 저장소를 사용하기 위해 chromadb를 가져옵니다.
import chromadb
# OpenAI Embeddings와 Responses API를 호출하기 위해 OpenAI 클라이언트를 가져옵니다.
from openai import OpenAI
# 프로젝트 설정과 RAG 저장 경로를 가져옵니다.
from app.config import DOCS_DIR, VECTOR_DB_DIR, settings
# Django가 저장한 게시글을 MySQL에서 읽는 저장소 함수를 가져옵니다.
from app.repositories.board_repository import fetch_all_boards
# PDF 청크 로딩과 내용 해시 함수를 가져옵니다.
from app.services.document_loader import load_pdf_chunks, sha256_text


@dataclass
class SearchResult:
    """API와 Django 화면에 반환할 하나의 벡터 검색 결과입니다."""
    # 검색된 원문 텍스트입니다.
    text: str
    # 출처 종류, 제목, 페이지, 게시글 ID 등의 메타데이터입니다.
    metadata: dict
    # ChromaDB가 반환한 cosine distance 값입니다.
    distance: float | None

    @property
    def similarity(self) -> float | None:
        """cosine distance를 사용자가 이해하기 쉬운 유사도 값으로 변환합니다."""
        # 거리 값이 없으면 유사도도 계산할 수 없습니다.
        if self.distance is None:
            return None
        # cosine distance에 대해 1-distance를 계산하고 안전 범위로 제한합니다.
        return max(-1.0, min(1.0, 1.0 - float(self.distance)))


class RagService:
    """PDF/게시글 증분 색인, 벡터 검색, 근거 기반 LLM 답변을 담당합니다."""
    # 문서와 게시글을 함께 저장할 ChromaDB 컬렉션 이름입니다.
    COLLECTION_NAME = "django_fastapi_docs_and_boards"

    def __init__(self) -> None:
        """OpenAI와 ChromaDB 클라이언트를 준비합니다."""
        # API 키가 비어 있으면 외부 호출 전에 명확한 설정 오류를 발생시킵니다.
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY가 없습니다. fastapi_ai/.env 파일을 설정하십시오.")
        # .env에서 읽은 키로 OpenAI 클라이언트를 생성합니다.
        self.openai = OpenAI(api_key=settings.openai_api_key)
        # 영구 저장형 ChromaDB 클라이언트를 프로젝트 vector_db 폴더에 생성합니다.
        self.chroma = chromadb.PersistentClient(path=str(VECTOR_DB_DIR))
        # cosine 거리 기반 컬렉션을 생성하거나 기존 컬렉션을 다시 엽니다.
        self.collection = self.chroma.get_or_create_collection(
            name=self.COLLECTION_NAME,
            configuration={"hnsw": {"space": "cosine"}},
        )

    def _embed(self, texts: list[str]) -> list[list[float]]:
        """여러 문자열을 OpenAI 임베딩 벡터로 변환합니다."""
        # 빈 입력이면 API를 호출하지 않고 빈 결과를 반환합니다.
        if not texts:
            return []
        # 설정된 임베딩 모델로 한 번에 여러 텍스트를 벡터화합니다.
        response = self.openai.embeddings.create(model=settings.openai_embedding_model, input=texts)
        # 입력 순서를 보장하기 위해 index 기준으로 응답을 정렬합니다.
        ordered = sorted(response.data, key=lambda item: item.index)
        # 각 응답 객체에서 실제 float 벡터만 추출합니다.
        return [item.embedding for item in ordered]

    @staticmethod
    def _batched(items: list, size: int = 64) -> Iterable[list]:
        """대량 청크를 OpenAI API에 안전한 작은 묶음으로 나눕니다."""
        # 0부터 전체 길이까지 배치 크기만큼 이동합니다.
        for index in range(0, len(items), size):
            # 현재 범위에 해당하는 슬라이스를 반환합니다.
            yield items[index:index + size]

    def _stored_hashes(self, source_type: str) -> dict[str, set[str]]:
        """현재 ChromaDB에 저장된 출처별 내용 해시를 조회합니다."""
        # source_type 조건으로 메타데이터만 조회하여 임베딩 전송을 피합니다.
        data = self.collection.get(where={"source_type": source_type}, include=["metadatas"])
        # source_key별 content_hash 집합을 저장할 딕셔너리를 준비합니다.
        result: dict[str, set[str]] = {}
        # 저장된 메타데이터를 하나씩 순회합니다.
        for metadata in data.get("metadatas") or []:
            # 비어 있는 메타데이터는 건너뜁니다.
            if not metadata:
                continue
            # 문서 파일 또는 게시글을 식별할 출처 키를 읽습니다.
            source_key = str(metadata.get("source_key", ""))
            # 내용 변경 여부 비교에 사용할 해시를 읽습니다.
            content_hash = str(metadata.get("content_hash", ""))
            # 같은 출처의 여러 청크 해시를 집합으로 누적합니다.
            result.setdefault(source_key, set()).add(content_hash)
        # 출처별 해시 딕셔너리를 반환합니다.
        return result

    def sync_documents(self, force: bool = False) -> dict:
        """FastAPI docs 폴더의 PDF를 ChromaDB와 증분 동기화합니다."""
        # 기존 문서 벡터의 해시 상태를 읽습니다.
        stored = self._stored_hashes("document")
        # 현재 디스크에 존재하는 문서 출처 키를 기록합니다.
        current_source_keys: set[str] = set()
        # 처리 통계 카운터를 초기화합니다.
        indexed_files = indexed_chunks = skipped_files = 0
        # docs 폴더의 PDF 파일을 이름 순서로 순회합니다.
        for pdf_path in sorted(DOCS_DIR.glob("*.pdf")):
            # PDF를 페이지별/문자수별 청크로 변환합니다.
            chunks = load_pdf_chunks(pdf_path)
            # 텍스트가 없는 PDF는 색인하지 않습니다.
            if not chunks:
                continue
            # 첫 청크 메타데이터에서 파일 단위 출처 키를 얻습니다.
            source_key = chunks[0].metadata["source_key"]
            # 현재 존재하는 출처로 기록합니다.
            current_source_keys.add(source_key)
            # 현재 파일 전체 청크의 내용 해시 집합을 계산합니다.
            current_hashes = {chunk.metadata["content_hash"] for chunk in chunks}
            # 강제 색인이 아니고 해시가 동일하면 임베딩 비용을 사용하지 않습니다.
            if not force and stored.get(source_key) == current_hashes:
                skipped_files += 1
                continue
            # 변경된 문서의 과거 청크를 먼저 모두 삭제합니다.
            self.collection.delete(where={"source_key": source_key})
            # 청크를 작은 배치로 나누어 임베딩하고 저장합니다.
            for batch in self._batched(chunks):
                # 현재 배치의 텍스트만 추출합니다.
                texts = [chunk.text for chunk in batch]
                # OpenAI 임베딩 벡터를 생성합니다.
                embeddings = self._embed(texts)
                # 동일 ID는 갱신되고 신규 ID는 추가되도록 upsert합니다.
                self.collection.upsert(
                    ids=[chunk.chunk_id for chunk in batch],
                    documents=texts,
                    metadatas=[chunk.metadata for chunk in batch],
                    embeddings=embeddings,
                )
                # 실제 저장한 청크 수를 통계에 누적합니다.
                indexed_chunks += len(batch)
            # 새로 색인한 파일 수를 증가시킵니다.
            indexed_files += 1
        # 디스크에서는 삭제되었지만 벡터DB에 남은 예전 파일을 정리합니다.
        for old_source_key in set(stored) - current_source_keys:
            # 해당 파일의 모든 청크를 조건 삭제합니다.
            self.collection.delete(where={"source_key": old_source_key})
        # 호출자에게 색인 결과 통계를 반환합니다.
        return {"indexed_files": indexed_files, "indexed_chunks": indexed_chunks, "skipped_files": skipped_files}

    @staticmethod
    def _board_payload(board: dict) -> tuple[str, dict]:
        """MySQL 게시글 한 행을 RAG 검색용 텍스트와 메타데이터로 변환합니다."""
        # 게시글 작성 시각을 문자열로 안전하게 변환합니다.
        created_at = board.get("created_at")
        # 제목/작성자/내용을 모두 포함하여 자연어 검색 품질을 높입니다.
        text_value = (
            f"게시글 번호: {board['board_id']}\n"
            f"제목: {board['title']}\n"
            f"작성자: {board['author_name']}\n"
            f"작성일: {created_at}\n"
            f"내용: {board['content']}"
        )
        # 게시글 기본키를 벡터DB 출처 키로 사용합니다.
        source_key = f"board:{board['board_id']}"
        # 검색 결과에서 원문 페이지를 연결할 수 있도록 메타데이터를 구성합니다.
        metadata = {
            "source_type": "board",
            "source_key": source_key,
            "board_id": int(board["board_id"]),
            "title": str(board["title"]),
            "author": str(board["author_name"]),
            "content_hash": sha256_text(text_value),
        }
        # 검색 텍스트와 메타데이터를 함께 반환합니다.
        return text_value, metadata

    def sync_boards(self, force: bool = False) -> dict:
        """Django 게시글 테이블의 추가/수정/삭제를 ChromaDB에 증분 반영합니다."""
        # 현재 저장된 게시글 해시를 가져옵니다.
        stored = self._stored_hashes("board")
        # 현재 DB에 존재하는 게시글 출처 키를 기록합니다.
        current_source_keys: set[str] = set()
        # 색인/건너뜀 통계를 초기화합니다.
        indexed = skipped = 0
        # 기존 Django ORM을 수정하지 않고 MySQL에서 게시글을 조회합니다.
        for board in fetch_all_boards():
            # 게시글 행을 RAG 텍스트/메타데이터로 변환합니다.
            text_value, metadata = self._board_payload(board)
            # 출처 키와 현재 내용 해시를 읽습니다.
            source_key = metadata["source_key"]
            current_hash = metadata["content_hash"]
            # 현재 존재하는 게시글로 기록합니다.
            current_source_keys.add(source_key)
            # 변경되지 않았다면 OpenAI 임베딩 호출을 생략합니다.
            if not force and stored.get(source_key) == {current_hash}:
                skipped += 1
                continue
            # 현재 게시글 텍스트를 하나의 벡터로 변환합니다.
            embedding = self._embed([text_value])[0]
            # 같은 게시글은 항상 같은 벡터 ID를 갖도록 안정적인 SHA-256 ID를 생성합니다.
            vector_id = "board-" + hashlib.sha256(source_key.encode("utf-8")).hexdigest()[:24]
            # 혹시 남아 있는 과거 게시글 벡터를 먼저 제거합니다.
            self.collection.delete(where={"source_key": source_key})
            # 변경된 최신 게시글을 벡터DB에 저장합니다.
            self.collection.upsert(ids=[vector_id], documents=[text_value], metadatas=[metadata], embeddings=[embedding])
            # 색인 수를 증가시킵니다.
            indexed += 1
        # Django에서 삭제된 게시글은 벡터DB에서도 제거합니다.
        for old_source_key in set(stored) - current_source_keys:
            # 게시글 출처 키 조건으로 해당 벡터를 삭제합니다.
            self.collection.delete(where={"source_key": old_source_key})
        # 게시글 동기화 통계를 반환합니다.
        return {"indexed": indexed, "skipped": skipped}

    def sync_all(self, force: bool = False) -> dict:
        """PDF 근거 문서와 MySQL 게시글을 한 번에 동기화합니다."""
        # 문서와 게시글의 동기화 결과를 각각 구조화하여 반환합니다.
        return {"documents": self.sync_documents(force=force), "boards": self.sync_boards(force=force)}

    def search(self, question: str, source_scope: str = "all", top_k: int = 5) -> list[SearchResult]:
        """자연어 질문과 의미상 가까운 PDF 청크 또는 게시글을 검색합니다."""
        # 질문을 문서와 같은 임베딩 공간의 벡터로 변환합니다.
        query_embedding = self._embed([question])[0]
        # 기본값은 문서와 게시글을 모두 검색하도록 조건을 두지 않습니다.
        where = None
        # 문서 전용 검색이면 source_type 조건을 지정합니다.
        if source_scope == "documents":
            where = {"source_type": "document"}
        # 게시글 전용 검색이면 source_type 조건을 지정합니다.
        elif source_scope == "boards":
            where = {"source_type": "board"}
        # ChromaDB 검색 인자를 구성합니다.
        query_kwargs = {
            "query_embeddings": [query_embedding],
            "n_results": max(1, min(top_k, 10)),
            "include": ["documents", "metadatas", "distances"],
        }
        # 검색 범위가 지정된 경우에만 where 조건을 추가합니다.
        if where:
            query_kwargs["where"] = where
        # 벡터 유사도 검색을 실행합니다.
        data = self.collection.query(**query_kwargs)
        # 첫 번째 질문의 문서/메타데이터/거리 결과를 각각 읽습니다.
        documents = (data.get("documents") or [[]])[0]
        metadatas = (data.get("metadatas") or [[]])[0]
        distances = (data.get("distances") or [[]])[0]
        # 세 결과를 같은 위치끼리 묶어 SearchResult 목록으로 변환합니다.
        return [SearchResult(text=text_value, metadata=metadata or {}, distance=distance) for text_value, metadata, distance in zip(documents, metadatas, distances)]

    def answer(self, question: str, results: list[SearchResult]) -> str:
        """검색된 근거만 LLM에 제공하여 환각을 줄인 최종 답변을 생성합니다."""
        # 검색 결과가 없다면 LLM을 호출하지 않고 근거 부족을 알립니다.
        if not results:
            return "검색된 근거가 없어 답변할 수 없습니다. 먼저 RAG 색인을 실행해 주세요."
        # LLM 입력에 사용할 근거 블록 목록을 준비합니다.
        context_blocks: list[str] = []
        # 검색 순위 번호를 1부터 부여해 출처 인용 번호로 사용합니다.
        for index, result in enumerate(results, start=1):
            # 출처 정보를 읽습니다.
            metadata = result.metadata
            # PDF 문서이면 문서 제목과 페이지를 표시합니다.
            if metadata.get("source_type") == "document":
                source_label = f"문서: {metadata.get('title')} / {metadata.get('page')}쪽"
            # 게시글이면 게시글 번호와 제목을 표시합니다.
            else:
                source_label = f"게시글 #{metadata.get('board_id')}: {metadata.get('title')}"
            # 번호가 붙은 근거 블록을 생성합니다.
            context_blocks.append(f"[근거 {index}] {source_label}\n{result.text}")
        # 모든 근거를 두 줄 간격으로 연결합니다.
        context = "\n\n".join(context_blocks)
        # 모델이 외부 지식을 임의로 추가하지 않도록 시스템 성격의 지시문을 작성합니다.
        instructions = (
            "당신은 Django+FastAPI 프로젝트의 RAG 답변 도우미입니다. "
            "반드시 제공된 검색 근거 안에서만 한국어로 답하십시오. "
            "근거에 없는 사실은 추측하지 말고 '제공된 근거에서 확인되지 않습니다'라고 답하십시오. "
            "핵심 주장 뒤에는 [근거 1] 형식으로 근거 번호를 표시하십시오."
        )
        # 사용자의 실제 질문과 검색된 근거를 하나의 입력으로 결합합니다.
        user_input = f"질문:\n{question}\n\n검색 근거:\n{context}"
        # OpenAI Responses API를 호출하여 근거 기반 답변을 생성합니다.
        response = self.openai.responses.create(model=settings.openai_chat_model, instructions=instructions, input=user_input)
        # 앞뒤 공백을 제거한 최종 답변 문자열을 반환합니다.
        return response.output_text.strip()
