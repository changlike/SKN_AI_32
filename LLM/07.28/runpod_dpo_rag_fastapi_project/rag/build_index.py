"""문서 청크 임베딩과 FAISS 인덱스를 생성합니다."""
# 메타데이터 저장을 위해 json을 가져옵니다.
import json
# 벡터 인덱스를 위해 faiss를 가져옵니다.
import faiss
# float32 배열 처리를 위해 numpy를 가져옵니다.
import numpy as np
# 다국어 임베딩 모델을 가져옵니다.
from sentence_transformers import SentenceTransformer
# 프로젝트 설정을 가져옵니다.
from training.common import ROOT, env

# 긴 문서를 겹치는 청크로 분할합니다.
def split(text: str, size: int = 500, overlap: int = 80):
    # 결과 청크 목록입니다.
    chunks = []
    # 첫 시작 위치입니다.
    start = 0
    # 문서 끝까지 반복합니다.
    while start < len(text):
        # 현재 청크 끝 위치를 계산합니다.
        end = min(start+size, len(text))
        # 문자열을 잘라 공백을 제거합니다.
        chunk = text[start:end].strip()
        # 비어 있지 않으면 추가합니다.
        if chunk:
            # 결과 목록에 추가합니다.
            chunks.append(chunk)
        # 끝에 도달하면 종료합니다.
        if end >= len(text):
            # 반복을 빠져나갑니다.
            break
        # overlap만큼 겹치도록 이동합니다.
        start = end-overlap
    # 청크 목록을 반환합니다.
    return chunks

# 인덱스를 생성합니다.
def main() -> None:
    # 출력 경로를 계산합니다.
    output = ROOT/env('RAG_INDEX','outputs/rag_index')
    # 출력 폴더를 생성합니다.
    output.mkdir(parents=True, exist_ok=True)
    # 임베딩 모델을 로드합니다.
    model = SentenceTransformer(env('EMBEDDING_MODEL','intfloat/multilingual-e5-small'))
    # 문서 메타데이터 목록입니다.
    docs = []
    # 모든 txt 문서를 순회합니다.
    for path in sorted((ROOT/'data/documents').glob('*.txt')):
        # 문서를 UTF-8로 읽습니다.
        text = path.read_text(encoding='utf-8')
        # 청크별로 순회합니다.
        for number, chunk in enumerate(split(text),1):
            # 출처와 원문을 저장합니다.
            docs.append({'source':path.name,'chunk_id':f'{path.stem}-{number}','text':chunk})
    # 문서가 없으면 오류를 발생시킵니다.
    if not docs:
        # 실행 순서 오류를 알립니다.
        raise RuntimeError('data/documents에 txt 문서가 없습니다.')
    # E5 문서 형식으로 임베딩합니다.
    vectors = model.encode([f"passage: {d['text']}" for d in docs], normalize_embeddings=True, convert_to_numpy=True)
    # FAISS 호환 float32로 변환합니다.
    vectors = np.asarray(vectors,dtype=np.float32)
    # 코사인 유사도용 inner-product 인덱스를 만듭니다.
    index = faiss.IndexFlatIP(vectors.shape[1])
    # 모든 문서 벡터를 추가합니다.
    index.add(vectors)
    # FAISS 인덱스를 저장합니다.
    faiss.write_index(index,str(output/'documents.faiss'))
    # 문서 메타데이터를 저장합니다.
    (output/'documents.json').write_text(json.dumps(docs,ensure_ascii=False,indent=2),encoding='utf-8')
    # 완료 메시지를 출력합니다.
    print(f'RAG 인덱스 완료: {len(docs)}개 청크')

# 직접 실행할 때만 main을 호출합니다.
if __name__ == '__main__':
    # 인덱스를 생성합니다.
    main()
