# path: ./app/model/schemas.py
# 요청(request) / 응답(response) 데이터 모델 정의

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class TextIn(BaseModel):
    """
    사용자로부터 입력받은 텍스트 담을 데이터 모델
    """
    text: str = Field(..., description="사용자가 입력해서 보내는 문자열값")
# class end -------------------------------------------

class ClassificationOut(BaseModel):
    # 예: label = 'POSITIVE' score=0.99999
    label: str
    score: float
# class end ----------------------------

class SummarizeIn(BaseModel):
    # 요약할 원문 저장용
    text: str = Field(..., description="사용자가 전송 보내는 요약할 원문")
    # 기본 파라미터 값 지정 (미지성 시 서버 기본값 사용함)
    max_length: Optional[int] = Field(None, description="생성 요약 최대 길이")
    min_length: Optional[int] = Field(None, description="생성 요약 최소 길이")
# class end ---------------------------------

class SummarizeOut(BaseModel):
    # 생성된 요약 결과 문장
    summary: str
# class end ------------------------------------

class TranslateIn(BaseModel):
    text: str = Field(..., description="번역할 원문 텍스트")
# class end -----------------------------------

class TranslateOut(BaseModel):
    translation: str
# class end --------------------------

class HealthOut(BaseModel):
    status: str
    loaded_models: Dict[str, Any]
# class end ------------------------------------
