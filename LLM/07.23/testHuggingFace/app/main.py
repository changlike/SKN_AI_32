# path: ./app/main.py
# fastapi 앱 앤트리포인트 (진입점)

from fastapi import FastAPI
from app.routers.nlp_router import router as nlp_router
from app.core.hf.pipelines import hf_manager
from app.models.schemas import HealthOut


app = FastAPI(title="HuggingFace Transformers NLP API (Windows/CPU/Python3.11", version="1.0,0")

# 라우터 등록
app.include_router(nlp_router)

@ app.on_event("startup")
def on_startup():
    """
    fastapi 서버가 시작될 때 딱 1회 실행되는 이벤트 헨들러임
    여기서 모델을 미리 로딩하면:
    - 첫 요청 지연을 줄이고
    - 요청마다 모델 로딩하는 실수를 방지함
    """
    hf_manager.load_all()
# def end ------------------------------

@app.get("/", response_model=HealthOut)
def home():
    """
    간단한 접속 상태 체크용
    - 모델 로딩 여부도 반환함
    """

    return HealthOut(status="ok", loaded_models=hf_manager.info)
# def end --------------------------------------------------------

# 실행
# uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Swagger UI
# http://127.0.0.1:8000/docs



