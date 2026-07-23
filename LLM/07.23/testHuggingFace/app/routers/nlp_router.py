# path: ./app/routers/nlp_router.py

'''
NLP API 라우터
 - /nlp/classify : 텍스트 분류
 - /nlp/summarize : 요약
 - /nlp/translate : 번역

* NLP (Natural Language Processing : 자연어 처리):
  사람이 사용하는 언어(자연어)를 컴퓨터가 이해하고 분석하고 생성하도록 만드는 AI 기술 분야임
* NLP API :
  자연어 처리 기능을 API 형태로 제공하는 서비스임
  텍스트를 주면 -> 분석/이해/결과를 돌려주는 API
  - 처리하는 대표 기능:
    1. 형태소 분석 / 토큰화
      "강아지는 귀엽다"
      -> ["강아지", "는", "귀엽다"]
    2. 감성 분석 (Sentiment Analysis)
      입력: "이 영화 정말 재미있다"
      출력: {"sentiment": "POSITIVE"}
    3. 문장 분류 / 의도 분석
      "환불하고 싶어요"
      -> intent: "refund_request"
    4. 개체명 인식 (NER)
      "홍길동은 서울에 산다"
      -> [홍길동: PERSON, 서울: LOCATION]
    5. 요약 (Summarization)
      긴 뉴스 기사 -> 핵심 문장 3줄
    6. 질의 응답 (Question Answering)
      질문 : "대한민국 수도는?"
      답 : "서울"
    7. 문장 생성 / 번역
      한국어 -> 영어
      질문 -> 답변 생성
'''

from fastapi import APIRouter, HTTPException
from app.models.schemas import (
    TextIn, ClassificationOut,
    SummarizeIn, SummarizeOut,
    TranslateIn, TranslateOut,
)
from app.core.config import settings
from app.core.hf.pipelines import hf_manager

# 라우터 객체 생성
router = APIRouter(prefix="/nlp", tags=['HUGGINGFACE-NLP'])

def classify(req: TextIn):
    """
    Text Classification API 앤드포인트 지정
    사용 흐름
    1. 사용자가 입력한 문자열 값들을 req가 받는다.
    2. req.text를 hf_manager.classify(req.text) 전달해서 파이프라인 실행.
    3. 리턴된 label, score를 응답 처리함
    """
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="text가 비어 있습니다.")

    # 파이프라인 실행하고 결과 받기
    result = hf_manager.classify(req.text)

    # 첫 결과만 사용
    top = result[0]
    return ClassificationOut(label=top["label"], score=top["score"])
# def end --------------------------------------------------------------

@router.post("/summarize", response_model=SummarizeOut)
def summarize(req: SummarizeIn):
    """
    문서 요약 api 앤드포인트 지정
    - 요액은 입력값이 길수록 시간이 걸림, 모델마다 토큰 재한이 있음
    => 너무 긴 글은 분할 전략이 필요함
    """
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="text가 비어 있습니다.")

    max_len = req.max_length if req.max_length is not None else settings.MAX_LENGTH
    min_len = req.min_length if req.min_length is not None else settings.MIN_LENGTH

    try:
        result = hf_manager.summarize(req.text, max_len, min_len)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Summarization failed: {str(e)}")

    summary = result[0].get("summary_text", "")
    return SummarizeOut(summary=summary)
# def end ----------------------------------------------------------------

@router.post("/translate", response_model=TranslateOut)
def translate(req: TranslateIn):
    """
    번역 api 앤드포인트 지정
    번역은 언어쌍별 모델이 다름 => 실세 서비스에서는 (source_language, target_language) 선택을 제공함
    """
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="text가 비어 있습니다.")

    result = hf_manager.translate(req.text)

    # pipeline 반환 형태 : [{'translate_text': '...'}]
    translation = result[0].get("translation", "")

    return TranslateOut(translation=translation)
# def end ---------------------------------------------


