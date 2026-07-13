# src/13_Q4.py
"""문제4: 기존 FAISS 인덱스에 새 문서를 증분 추가 (add_documents)"""

from common import get_embeddings, load_documents, chunk_documents, PROJECT_ROOT, print_documents
from langchain_community.vectorstores import FAISS

MEMBERSHIP_INDEX_DIR = PROJECT_ROOT / "data" / "faiss_index" / "membership"  # 문제1과 동일 경로 (재사용)
NEW_FILE = "환불교환정책.pdf"


def incremental_update():
    emb = get_embeddings()

    # 1) 기존 인덱스 로드 (재생성 아님 - 이미 있는 벡터는 그대로 유지)
    vs = FAISS.load_local(
        str(MEMBERSHIP_INDEX_DIR),
        emb,
        allow_dangerous_deserialization=True,
    )
    print(f"기존 청크 개수: {vs.index.ntotal}")

    # 2) 새 문서 로드 + 청킹
    new_docs = load_documents([NEW_FILE])
    new_chunks = chunk_documents(new_docs)
    print(f"새로 추가할 청크 개수: {len(new_chunks)}")

    # 3) 증분 추가 - 새 청크만 embed_documents() 호출됨 (기존 벡터 재계산 X)
    vs.add_documents(new_chunks)
    print(f"업데이트 후 총 청크 개수: {vs.index.ntotal}")

    # 4) 같은 경로에 다시 저장 (기존+신규 전체를 덮어씀)
    vs.save_local(str(MEMBERSHIP_INDEX_DIR))
    print(f"증분 업데이트 저장 완료: {MEMBERSHIP_INDEX_DIR}")

    return vs


def verify_new_content(vs, query: str = "환불 조건"):
    # 5) 신규 문서 키워드로 검색해서 새로 추가된 내용이 잡히는지 확인
    results = vs.similarity_search(query, k=3)
    print_documents(f"'{query}' 검색 결과 (신규 문서 포함 확인)", results)


def main():
    vs = incremental_update()
    verify_new_content(vs)


if __name__ == "__main__":
    main()