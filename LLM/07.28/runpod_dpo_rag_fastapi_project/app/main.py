"""Fine-tuned 모델과 RAG를 제공하는 FastAPI 앱입니다."""
# 평가 결과 JSON을 읽기 위해 json을 가져옵니다.
import json
# 동시 GPU 생성을 제어하기 위해 Lock을 가져옵니다.
from threading import Lock
# 경로 처리를 위해 Path를 가져옵니다.
from pathlib import Path
# 벡터 검색을 위해 faiss를 가져옵니다.
import faiss
# 임베딩 배열을 위해 numpy를 가져옵니다.
import numpy as np
# GPU 추론을 위해 torch를 가져옵니다.
import torch
# FastAPI와 HTTP 오류를 가져옵니다.
from fastapi import FastAPI, HTTPException
# HTML 파일 응답을 가져옵니다.
from fastapi.responses import FileResponse
# 정적 파일 제공 기능을 가져옵니다.
from fastapi.staticfiles import StaticFiles
# OpenAI 호환 vLLM 호출 클라이언트를 가져옵니다.
from openai import OpenAI
# 요청 검증 모델을 가져옵니다.
from pydantic import BaseModel, Field
# 문장 임베딩 모델을 가져옵니다.
from sentence_transformers import SentenceTransformer
# 로컬 모델과 토크나이저를 가져옵니다.
from transformers import AutoModelForCausalLM, AutoTokenizer
# 설정 함수를 가져옵니다.
from app.config import get_settings

# 채팅 요청 스키마입니다.
class ChatRequest(BaseModel):
    # 질문은 1~4000자만 허용합니다.
    question: str = Field(min_length=1,max_length=4000)
    # top_k는 1~10 범위입니다.
    top_k: int | None = Field(default=None,ge=1,le=10)

# 설정 객체를 만듭니다.
settings = get_settings()
# FastAPI 앱을 만듭니다.
app = FastAPI(title='DPO Fine-tuned RAG Service',version='1.0.0')
# 정적 파일 폴더를 계산합니다.
static_dir = Path(__file__).parent/'static'
# /static 경로를 연결합니다.
app.mount('/static',StaticFiles(directory=static_dir),name='static')
# GPU generate 동시 실행을 제어합니다.
lock = Lock()
# 지연 로딩 모델 객체입니다.
model = None
# 지연 로딩 토크나이저 객체입니다.
tokenizer = None
# 임베딩 모델을 로드합니다.
embedder = SentenceTransformer(settings.embedding_model)
# FAISS 인덱스 초기값입니다.
index = None
# 문서 메타데이터 초기값입니다.
documents = []

# RAG 인덱스를 디스크에서 다시 읽습니다.
def load_index() -> None:
    # 전역 인덱스와 문서 목록을 수정합니다.
    global index, documents
    # 인덱스 파일 경로입니다.
    index_path = settings.rag_index/'documents.faiss'
    # 메타데이터 파일 경로입니다.
    docs_path = settings.rag_index/'documents.json'
    # 두 파일이 모두 있을 때만 로드합니다.
    if index_path.exists() and docs_path.exists():
        # FAISS 인덱스를 읽습니다.
        index = faiss.read_index(str(index_path))
        # 문서 메타데이터를 읽습니다.
        documents = json.loads(docs_path.read_text(encoding='utf-8'))

# 서버 시작 시 기존 인덱스를 읽습니다.
load_index()

# transformers 모델을 첫 요청에서 한 번만 로드합니다.
def ensure_model() -> None:
    # 전역 모델과 토크나이저를 수정합니다.
    global model, tokenizer
    # 이미 로드된 경우 종료합니다.
    if model is not None and tokenizer is not None:
        # 중복 로딩을 막습니다.
        return
    # 병합 모델이 있으면 사용하고 없으면 원본 모델을 사용합니다.
    path = str(settings.merged_model) if settings.merged_model.exists() else settings.base_model
    # 토크나이저를 로드합니다.
    tokenizer = AutoTokenizer.from_pretrained(path,trust_remote_code=True,token=settings.hf_token)
    # 패딩 토큰을 보장합니다.
    tokenizer.pad_token_id = tokenizer.pad_token_id or tokenizer.eos_token_id
    # GPU에서는 float16을 사용합니다.
    dtype = torch.float16 if torch.cuda.is_available() else torch.float32
    # 언어 모델을 로드합니다.
    model = AutoModelForCausalLM.from_pretrained(path,torch_dtype=dtype,device_map='auto' if torch.cuda.is_available() else None,trust_remote_code=True,token=settings.hf_token)
    # 평가 모드로 전환합니다.
    model.eval()

# 시스템·사용자 프롬프트로 답변을 생성합니다.
def generate(system: str, user: str) -> str:
    # vLLM 백엔드이면 OpenAI 호환 API를 호출합니다.
    if settings.llm_backend.lower() == 'vllm':
        # vLLM 클라이언트를 생성합니다.
        client = OpenAI(base_url=settings.vllm_base_url,api_key=settings.vllm_api_key)
        # Chat Completions를 호출합니다.
        response = client.chat.completions.create(model=settings.vllm_model_name,messages=[{'role':'system','content':system},{'role':'user','content':user}],temperature=0.2,max_tokens=256)
        # 첫 답변 텍스트를 반환합니다.
        return (response.choices[0].message.content or '').strip()
    # 로컬 모델을 준비합니다.
    ensure_model()
    # 채팅 템플릿용 메시지를 구성합니다.
    messages = [{'role':'system','content':system},{'role':'user','content':user}]
    # 채팅 템플릿을 적용합니다.
    text = tokenizer.apply_chat_template(messages,tokenize=False,add_generation_prompt=True)
    # 입력을 토큰화합니다.
    batch = tokenizer(text,return_tensors='pt',truncation=True,max_length=1024)
    # 모델 장치로 이동합니다.
    batch = {k:v.to(next(model.parameters()).device) for k,v in batch.items()}
    # 동시 GPU 생성을 직렬화합니다.
    with lock:
        # gradient 없이 생성합니다.
        with torch.inference_mode():
            # 최대 256 토큰을 생성합니다.
            output = model.generate(**batch,max_new_tokens=256,do_sample=True,temperature=0.2,top_p=0.9,pad_token_id=tokenizer.pad_token_id,eos_token_id=tokenizer.eos_token_id)
    # 신규 생성 토큰만 선택합니다.
    new_ids = output[0,batch['input_ids'].shape[1]:]
    # 문자열로 변환해 반환합니다.
    return tokenizer.decode(new_ids,skip_special_tokens=True).strip()

# 질문과 유사한 문서를 검색합니다.
def search(query: str, top_k: int):
    # 인덱스가 없으면 실행 순서 오류를 알립니다.
    if index is None or not documents:
        # 인덱스 생성 명령을 안내합니다.
        raise RuntimeError('python rag/build_index.py를 먼저 실행하십시오.')
    # 질문을 정규화 임베딩으로 변환합니다.
    vector = embedder.encode([f'query: {query}'],normalize_embeddings=True,convert_to_numpy=True)
    # FAISS 호환 float32로 변환합니다.
    vector = np.asarray(vector,dtype=np.float32)
    # 상위 문서 점수와 인덱스를 검색합니다.
    scores, ids = index.search(vector,min(top_k,len(documents)))
    # API 반환 구조로 변환합니다.
    return [{'source':documents[int(i)]['source'],'text':documents[int(i)]['text'],'score':float(s)} for s,i in zip(scores[0],ids[0]) if i>=0]

# 루트 UI를 반환합니다.
@app.get('/',include_in_schema=False)
def root():
    # index.html을 반환합니다.
    return FileResponse(static_dir/'index.html')

# 서버 상태를 반환합니다.
@app.get('/health')
def health():
    # 모델·RAG 상태를 JSON으로 반환합니다.
    return {'status':'ok','backend':settings.llm_backend,'merged_model_exists':settings.merged_model.exists(),'rag_loaded':index is not None}

# 모델 단독 채팅 API입니다.
@app.post('/api/chat')
def chat(request: ChatRequest):
    # 추론 오류를 HTTP 500으로 변환합니다.
    try:
        # 모델 답변을 생성합니다.
        answer = generate('당신은 정확하고 친절한 한국어 AI 조교입니다.',request.question)
        # 답변과 빈 근거 목록을 반환합니다.
        return {'answer':answer,'backend':settings.llm_backend,'sources':[]}
    except Exception as exc:
        # 내부 오류를 HTTP 오류로 변환합니다.
        raise HTTPException(status_code=500,detail=str(exc)) from exc

# RAG 채팅 API입니다.
@app.post('/api/rag/chat')
def rag_chat(request: ChatRequest):
    # 검색·추론 오류를 HTTP 500으로 변환합니다.
    try:
        # 관련 문서를 검색합니다.
        sources = search(request.question,request.top_k or settings.rag_top_k)
        # 번호와 출처가 있는 컨텍스트를 만듭니다.
        context = "\n\n".join(
            f"[근거 {n} | {d['source']}]\n{d['text']}"
            for n, d in enumerate(sources, 1)
        )
        # 근거 제한 시스템 지시를 정의합니다.
        system = "제공된 근거만 사용해 한국어로 답하십시오. 근거에 없으면 '제공된 문서에서 확인할 수 없습니다.'라고 답하십시오. 마지막에 근거 번호를 표시하십시오."
        # 컨텍스트와 질문을 합칩니다.
        user = f"{context}\n\n[질문]\n{request.question}"
        # 근거 기반 답변을 생성합니다.
        answer = generate(system,user)
        # 답변과 검색 근거를 반환합니다.
        return {'answer':answer,'backend':settings.llm_backend,'sources':sources}
    except Exception as exc:
        # 내부 오류를 HTTP 오류로 변환합니다.
        raise HTTPException(status_code=500,detail=str(exc)) from exc

# 최신 RAG 인덱스를 다시 읽습니다.
@app.post('/api/rag/reload')
def reload_rag():
    # 디스크 인덱스를 다시 로드합니다.
    load_index()
    # 로드 상태를 반환합니다.
    return {'loaded':index is not None,'document_count':len(documents)}

# 최근 평가 결과를 반환합니다.
@app.get('/api/evaluation')
def evaluation():
    # 평가 결과 파일 경로입니다.
    path = Path('outputs/evaluation/results.json')
    # 파일이 없으면 404를 반환합니다.
    if not path.exists():
        # 실행할 평가 명령을 안내합니다.
        raise HTTPException(status_code=404,detail='python training/04_evaluate.py를 실행하십시오.')
    # JSON 결과를 반환합니다.
    return json.loads(path.read_text(encoding='utf-8'))
