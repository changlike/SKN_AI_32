# src/14_Q5.py
"""문제5: 메타데이터(source) 필터링 검색 - 선택한 파일 안에서만 검색"""

from common import get_embeddings, PROJECT_ROOT
from langchain_community.vectorstores import FAISS

MEMBERSHIP_INDEX_DIR = PROJECT_ROOT / "data" / "faiss_index" / "membership"  # 문제1~4에서 계속 쓴 경로

FILE_MENU = {
    "1": "멤버십정책.pdf",
    "2": "환불교환정책.pdf",
}


def print_with_metadata(query: str, docs, max_chars: int = 160):
    print(f"\n[검색어: '{query}']")
    for i, doc in enumerate(docs, start=1):
        source = doc.metadata.get("source", "출처 없음")
        page = doc.metadata.get("page", 0)
        display_page = page + 1 if isinstance(page, int) else page  # 문제3에서 확정한 규칙: 출력만 +1
        content = doc.page_content.replace("\n", " ")[:max_chars]
        print(f"{i}. 파일명={source}, 페이지={display_page}")
        print(f"   내용: {content}...")


def filter_search():
    emb = get_embeddings()
    vs = FAISS.load_local(
        str(MEMBERSHIP_INDEX_DIR),
        emb,
        allow_dangerous_deserialization=True,
    )

    # 파일 선택 메뉴 출력
    print("\n검색할 문서를 선택하세요:")
    for key, name in FILE_MENU.items():
        print(f"{key}. {name}")
    choice = input("번호 입력: ").strip()

    if choice not in FILE_MENU:
        print("잘못된 번호입니다.")
        return

    selected_file = FILE_MENU[choice]
    query = input("검색어를 입력하세요: ").strip()

    # filter: metadata.source가 선택한 파일명과 일치하는 청크에서만 검색
    results = vs.similarity_search(query, k=3, filter={"source": selected_file})

    print(f"\n선택 문서: {selected_file}")
    print_with_metadata(query, results)


def main():
    filter_search()


if __name__ == "__main__":
    main()