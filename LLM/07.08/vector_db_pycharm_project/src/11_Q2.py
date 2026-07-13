# 문제 2 — load 후 검색 검증
# 문제 1에서 저장한 인덱스를 load_local로 불러와 "VIP 적립률"을 검색하세요.

# 사용 파일: data/faiss_index/membership
# 기대 결과: 적립률 정보가 든 청크가 top-1으로 검색되고,
# 새로 만들지 않고 로드만으로 검색됨을 확인하면 성공.
# ------------------------------------------------------------------------

# 문제2: 저장된 FAISS 인덱스를 load_local로 불러와 검색만 수행

from common import get_embeddings, print_documents, PROJECT_ROOT
from langchain_community.vectorstores import FAISS

MEMBERSHIP_INDEX_DIR = PROJECT_ROOT / "data" / "faiss_index" / "membership"

def search_membership(query: str, k: int = 1):
    emb = get_embeddings()

    vs = FAISS.load_local(
        str(MEMBERSHIP_INDEX_DIR),
        emb,
        allow_dangerous_deserialization=True,
    )

    results = vs.similarity_search(query, k=k)
    print_documents(f"'{query}' 검색 결과", results)

def main():
    search_membership("VIP 적립률")

if __name__ == "__main__":
    main()

