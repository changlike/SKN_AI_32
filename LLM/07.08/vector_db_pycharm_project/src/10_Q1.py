# 문제 1 — FAISS 인덱스 생성·저장
# data/docs/멤버십정책.pdf를 청킹·임베딩하여 FAISS 인덱스를 만들고
# data/faiss_index/membership에 save_local하세요.

# 기대 결과: 저장 폴더에 index.faiss, index.pkl이 생성되고, 저장된 청크 개수를 출력하면 성공.
# -------------------------------------------------------------------

# 문제 1 step1: pdf 로드 -> 청킹 -> 구글 임베딩 -> FAISS 저장
from pathlib import Path
from langchain_community.vectorstores import FAISS     # FAISS 벡터스토어
from common import (
    PROJECT_ROOT,
    load_documents,
    chunk_documents,
    get_embeddings,
)

TARGET_FILE = "멤버십정책.pdf"

# 문제 1이 지정한 저장 경로는 common.py의 FAISS_DIR과 다르므로 별도 상수로 정의
MEMBERSHIP_INDEX_DIR = PROJECT_ROOT / "data" / "faiss_index" / "membership"

def build_membership_index():
    docs = load_documents([TARGET_FILE])
    chunks = chunk_documents(docs)
    print(f"청크 개수: {len(chunks)}")

    emb = get_embeddings()

    vs = FAISS.from_documents(chunks, emb)
    MEMBERSHIP_INDEX_DIR.mkdir(parents=True, exist_ok=True)
    vs.save_local(str(MEMBERSHIP_INDEX_DIR))

    print(f"저장 완료: {MEMBERSHIP_INDEX_DIR}")
    print(f"저장된 청크 개수: {vs.index.ntotal}")

def main():
    build_membership_index()

if __name__ == "__main__":
    main()

