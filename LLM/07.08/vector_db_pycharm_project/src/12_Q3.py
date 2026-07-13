# src/12_Q3.py
"""문제3: 검색 결과에 문서파일명 + 페이지 정보 출력 (문제2 내용 복사 후 확장)"""

from common import get_embeddings, PROJECT_ROOT
from langchain_community.vectorstores import FAISS

MEMBERSHIP_INDEX_DIR = PROJECT_ROOT / "data" / "faiss_index" / "membership"  # 문제1과 동일 경로


def print_with_metadata(query: str, docs, max_chars: int = 160):
    """검색 결과마다 출처 파일명 + 페이지 번호를 명시적으로 출력하는 함수"""
    print(f"\n[검색어: '{query}']")
    for i, doc in enumerate(docs, start=1):
        source = doc.metadata.get("source", "출처 없음")  # PDF 파일명 (load_pdf_documents에서 저장됨)
        page = doc.metadata.get("page", "페이지 없음")     # PyPDFLoader가 자동 부여한 페이지 번호 (0-index)
        content = doc.page_content.replace("\n", " ")[:max_chars]
        print(f"{i}. 파일명={source}, 페이지={page}")
        print(f"   내용: {content}...")


def search_with_metadata(query: str, k: int = 1):
    emb = get_embeddings()

    vs = FAISS.load_local(
        str(MEMBERSHIP_INDEX_DIR),
        emb,
        allow_dangerous_deserialization=True,
    )

    results = vs.similarity_search(query, k=k)
    print_with_metadata(query, results)
    return results


def main():
    search_with_metadata("VIP 적립률")


if __name__ == "__main__":
    main()