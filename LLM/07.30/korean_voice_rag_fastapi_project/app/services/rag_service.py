"""PDF, TXT, MD 문서를 읽어 고객 문의의 근거를 검색합니다."""
from dataclasses import dataclass  # 문서 조각을 명확한 자료형으로 관리합니다.
from pathlib import Path  # 문서 파일 경로를 처리합니다.
from threading import Lock  # 동시에 여러 요청이 들어올 때 인덱스 중복 생성을 막습니다.
import logging  # 임베딩 모델 실패 원인을 서버에 기록합니다.
import re  # 한국어와 영문 검색어를 토큰으로 분리합니다.
import numpy as np  # 임베딩 벡터 계산과 점수 정렬에 사용합니다.
from pypdf import PdfReader  # PDF 각 페이지의 텍스트를 추출합니다.
from app.config import settings  # 문서 경로와 검색 설정을 가져옵니다.

logger = logging.getLogger(__name__)  # 현재 모듈 전용 로거를 만듭니다.

@dataclass
class Chunk:
    source: str  # 원본 문서 파일명입니다.
    page: int | None  # PDF 페이지 번호이며 TXT와 MD는 None입니다.
    chunk_id: int  # 문서 내부 조각 번호입니다.
    text: str  # 검색과 답변 생성에 사용할 본문입니다.

class RagService:
    """의미 검색과 한국어 키워드 검색을 결합한 RAG 검색기입니다."""
    def __init__(self) -> None:
        self._chunks: list[Chunk] = []  # 로딩한 모든 문서 조각을 저장합니다.
        self._model = None  # SentenceTransformer 모델을 필요할 때만 저장합니다.
        self._embeddings: np.ndarray | None = None  # 문서 임베딩 행렬을 저장합니다.
        self._built = False  # 문서 인덱스 생성 완료 여부를 기록합니다.
        self._search_mode = "not_built"  # 실제로 사용 중인 검색 방식을 기록합니다.
        self._last_error: str | None = None  # 임베딩 실패 내용을 상태 API에 제공합니다.
        self._lock = Lock()  # 인덱스 생성 구간을 보호합니다.

    @property
    def search_mode(self) -> str:
        return self._search_mode  # 상태 API에서 검색 방식을 확인하도록 반환합니다.

    @property
    def last_error(self) -> str | None:
        return self._last_error  # 마지막 오류를 반환합니다.

    def _split(self, text: str) -> list[str]:
        normalized = re.sub(r"\s+", " ", text).strip()  # 줄바꿈과 연속 공백을 하나의 공백으로 정리합니다.
        if not normalized:
            return []  # 텍스트가 없으면 빈 목록을 반환합니다.
        result: list[str] = []  # 완성된 조각을 저장할 목록입니다.
        start = 0  # 현재 조각의 시작 위치입니다.
        while start < len(normalized):
            end = min(start + settings.CHUNK_SIZE, len(normalized))  # 설정한 최대 크기까지 끝 위치를 계산합니다.
            if end < len(normalized):
                candidates = [normalized.rfind(mark, start, end) for mark in (". ", "다. ", "요. ", "! ", "? ")]  # 가능한 문장 끝 위치를 찾습니다.
                sentence_end = max(candidates)  # 가장 뒤쪽에 있는 문장 끝을 선택합니다.
                if sentence_end > start + settings.CHUNK_SIZE // 2:
                    end = sentence_end + 1  # 너무 짧지 않을 때 문장 경계에서 조각을 끝냅니다.
            part = normalized[start:end].strip()  # 현재 범위의 텍스트를 추출합니다.
            if part:
                result.append(part)  # 비어 있지 않은 조각만 추가합니다.
            if end >= len(normalized):
                break  # 문서 끝에 도달하면 반복을 종료합니다.
            start = max(end - settings.CHUNK_OVERLAP, start + 1)  # 일부 내용을 겹치며 다음 시작점을 계산합니다.
        return result  # 분할된 문서 조각을 반환합니다.

    def _load_pdf(self, path: Path) -> None:
        reader = PdfReader(str(path))  # PDF 파일을 엽니다.
        chunk_id = 0  # 파일 내부 조각 번호를 0부터 시작합니다.
        for page_number, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""  # 텍스트가 없는 페이지는 빈 문자열로 처리합니다.
            for part in self._split(text):
                self._chunks.append(Chunk(path.name, page_number, chunk_id, part))  # 파일명과 페이지 번호를 포함해 조각을 저장합니다.
                chunk_id += 1  # 다음 조각 번호로 증가시킵니다.

    def _load_text(self, path: Path) -> None:
        text = path.read_text(encoding="utf-8-sig", errors="replace")  # UTF-8 BOM과 일부 잘못된 문자를 안전하게 처리합니다.
        for chunk_id, part in enumerate(self._split(text)):
            self._chunks.append(Chunk(path.name, None, chunk_id, part))  # 일반 텍스트 문서 조각을 저장합니다.

    def _keyword_tokens(self, text: str) -> set[str]:
        raw = re.findall(r"[가-힣]{2,}|[A-Za-z0-9]{2,}", text.lower())  # 두 글자 이상의 한국어, 영문, 숫자 토큰을 추출합니다.
        tokens = set(raw)  # 같은 단어의 중복을 제거합니다.
        for word in raw:
            if len(word) >= 4:
                tokens.update(word[index:index + 2] for index in range(len(word) - 1))  # 긴 한국어 단어는 2글자 부분 문자열도 추가합니다.
        return tokens  # 검색 점수 계산용 토큰 집합을 반환합니다.

    def _build(self) -> None:
        if self._built:
            return  # 이미 인덱스를 만들었다면 재사용합니다.
        with self._lock:
            if self._built:
                return  # 다른 요청이 먼저 생성했는지 다시 확인합니다.
            settings.DOCUMENT_DIR.mkdir(parents=True, exist_ok=True)  # 문서 폴더가 없으면 생성합니다.
            self._chunks = []  # 이전 문서 조각을 초기화합니다.
            for path in sorted(settings.DOCUMENT_DIR.iterdir()):
                if path.suffix.lower() == ".pdf":
                    self._load_pdf(path)  # PDF는 페이지별로 텍스트를 추출합니다.
                elif path.suffix.lower() in {".txt", ".md"}:
                    self._load_text(path)  # TXT와 MD는 UTF-8 텍스트로 읽습니다.
            self._embeddings = None  # 새 문서에 맞춰 임베딩을 초기화합니다.
            requested = settings.RAG_MODE  # 사용자가 요청한 검색 방식을 읽습니다.
            if self._chunks and requested in {"hybrid", "embedding"}:
                try:
                    from sentence_transformers import SentenceTransformer  # 의미 검색을 사용할 때만 패키지를 가져옵니다.
                    self._model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)  # 다국어 임베딩 모델을 로딩합니다.
                    passages = [f"passage: {chunk.text}" for chunk in self._chunks]  # E5 모델 권장 접두어를 붙입니다.
                    self._embeddings = self._model.encode(passages, convert_to_numpy=True, normalize_embeddings=True, show_progress_bar=False).astype(np.float32)  # 문서 벡터를 생성합니다.
                    self._search_mode = "hybrid" if requested == "hybrid" else "embedding"  # 실제 검색 모드를 기록합니다.
                    self._last_error = None  # 정상 로딩되었으므로 이전 오류를 지웁니다.
                except Exception as exc:
                    self._model = None  # 불완전한 모델 객체를 제거합니다.
                    self._embeddings = None  # 불완전한 임베딩을 제거합니다.
                    self._search_mode = "keyword_fallback"  # 인터넷이나 모델 문제 시 키워드 검색으로 전환합니다.
                    self._last_error = f"{type(exc).__name__}: {exc}"  # 상태 API에 원인을 보관합니다.
                    logger.warning("임베딩 검색을 사용할 수 없어 키워드 검색으로 전환합니다: %s", exc)  # 서버 터미널에 원인을 기록합니다.
            else:
                self._search_mode = "keyword"  # 문서가 없거나 keyword 모드가 지정되면 키워드 검색을 사용합니다.
            self._built = True  # 인덱스 생성 완료 상태로 변경합니다.

    def search(self, question: str) -> list[dict]:
        self._build()  # 최초 질문에서 문서를 로딩하고 인덱스를 만듭니다.
        if not self._chunks:
            return []  # 문서가 없으면 빈 근거 목록을 반환합니다.
        query_tokens = self._keyword_tokens(question)  # 질문에서 키워드를 추출합니다.
        keyword_scores = np.array([len(query_tokens & self._keyword_tokens(chunk.text)) / max(len(query_tokens), 1) for chunk in self._chunks], dtype=np.float32)  # 질문과 문서의 토큰 겹침 비율을 계산합니다.
        final_scores = keyword_scores.copy()  # 기본 점수는 키워드 점수입니다.
        if self._model is not None and self._embeddings is not None:
            query_vector = self._model.encode([f"query: {question}"], convert_to_numpy=True, normalize_embeddings=True, show_progress_bar=False)[0].astype(np.float32)  # 질문 임베딩을 생성합니다.
            semantic_scores = self._embeddings @ query_vector  # 코사인 유사도를 계산합니다.
            final_scores = semantic_scores if self._search_mode == "embedding" else semantic_scores * 0.75 + keyword_scores * 0.25  # hybrid 모드에서는 두 점수를 결합합니다.
        indices = np.argsort(final_scores)[::-1][:settings.RAG_TOP_K]  # 점수가 높은 순서로 상위 조각을 선택합니다.
        results: list[dict] = []  # API에 반환할 결과 목록입니다.
        for index in indices:
            chunk = self._chunks[int(index)]  # 선택된 문서 조각을 가져옵니다.
            results.append({"source": chunk.source, "page": chunk.page, "chunk_id": chunk.chunk_id, "text": chunk.text, "score": float(final_scores[int(index)])})  # 출처, 페이지, 본문, 점수를 저장합니다.
        return results  # 최종 검색 결과를 반환합니다.

    def rebuild(self) -> int:
        with self._lock:
            self._chunks = []  # 기존 문서 조각을 제거합니다.
            self._model = None  # 기존 임베딩 모델 참조를 제거합니다.
            self._embeddings = None  # 기존 벡터를 제거합니다.
            self._built = False  # 다음 검색에서 다시 생성하도록 상태를 초기화합니다.
            self._search_mode = "not_built"  # 검색 모드를 초기화합니다.
        self._build()  # 현재 data/docs 문서를 기준으로 새 인덱스를 생성합니다.
        return len(self._chunks)  # 생성된 전체 조각 수를 반환합니다.

    def status(self) -> dict:
        self._build()  # 상태 확인 시에도 문서 인덱스를 준비합니다.
        return {"document_count": len({chunk.source for chunk in self._chunks}), "chunk_count": len(self._chunks), "search_mode": self._search_mode, "last_error": self._last_error}  # 문서와 검색 상태를 반환합니다.
