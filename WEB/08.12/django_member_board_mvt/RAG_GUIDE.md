# OpenAI LLM + ChromaDB RAG 검색 서비스 구현 가이드

## 1. 구현 목적

두 종류의 근거를 동시에 사용함

1. 'docs/' 폴더의 pdf 근거 문서
2. Django MySQL 'boards_board' 테이블 게시글

질문을 입력하면 OpenAI Embeddings API로 질문을 벡터화하고,
ChromaDB 에서 의미적으로 가까운 청크를 검색한 뒤,
검색 결과만 OpenAI Response API에 전달하여 한국어 답변을 생성하게 함

## 2. 전체 처리 흐름
```text
[PDF 문서] -- PyPDF -- 청크 분할
                              |- OpenAI Embeddings --- ChromaDB
[게시글] -- Django ORM -----------------------|        

[사용자 질문] ---  OpenAI Embeddings -----------  ChromaDB 벡터 검색
                                                ▼        
                                    cosine Top-K 검색      
                                                ▼
                                    검색 근거 + 사용자 질문  
                                                ▼
                                     OpenAI Response API
                                                 ▼
                                     근거 번호 포함 답변  
```

## 3. 문서의 청킹 크기 지정

앱 생성 : rag
```터미널
python manage.py startapp rag
```
'rag/document_loader.py'

PDF 페이지 읽어 들여서, 텍스트 추출하고 기본 1000자, 150자 overlap 으로 청크를 만듦
각 청크에는 문서 제목, 파일명, 페이지 번호, 청크번호, 내용 해시가 메타 데이터로 저장됨

## 4. ChromaDB 저장 구조

벡터DB 물리적 경로:
'vector_db/chroma/'

컬렉션 이름 : 
django_docs_and_boards

문서와 게시글을 한 컬렉션에 저장하되 메타 데이터의 'source_type' 으로 구분함
```text
source_type=document   # PDF 문서
source_type=board       # Django 게시글
```

## 5. 패키지 추가 설치
requirements.txt 추가 작성
```text
# OpenAI Responses API 와 Embedding API 호출을 위함
openai>=1.100
# 문서와 게시글 임베딩을 로컬 영구 벡터DB에 저장하고, 코사인 검색을 위함
chromadb>=1.0
# docs 폴더에서 제공된 pdf 문서의 텍스트와 메타데이터를 추출하기 위함
pypdf>=5.0,<7.0
```

설치:
```터미널
pip install -r requirements.txt
```

## 6. 환경변수에 추가 설정

```text
OPENAI_API_KEY=실제_API_Key
OPENAI_CHAT_MODEL=gpt-5.6-luna
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

# 주의 : .env 는 Git 에 커밋하지 않는다.

## 7. 마이그레이션

RAG 앱은 검색 벡터를 ChromaDB에 저장하므로,
별도의 MySQL RAG 테이블을 migration 할 필요가 없음

## 8. 최초 벡터 색인 생성
rag/management/commans 패키지 추가
rag/management/commans/rag_index.py 파일 생성


```터미널
python manage.py rag_reindex

# pdf 문서만 색인 생성
python manage.py rag_reindex --source documents

# 게시글만 색인 생성
python manage.py rag_reindex --source boards

# 전체 강제 재색인
python manage.py rag_reindex --force
```

## 9. 실행

http://127.0.0.1:8000/rag
