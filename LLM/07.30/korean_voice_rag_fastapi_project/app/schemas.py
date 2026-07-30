"""FastAPI 요청과 응답 데이터 구조를 정의합니다."""
from pydantic import BaseModel, Field  # 입력 검증과 JSON 직렬화에 사용합니다.

class TextQuestionRequest(BaseModel):
    """텍스트 고객 문의 요청입니다."""
    question: str = Field(..., min_length=1, max_length=2000)  # 빈 질문과 지나치게 긴 질문을 차단합니다.
    speak: bool = True  # 답변을 음성으로 생성할지 결정합니다.

class SourceItem(BaseModel):
    """RAG 검색 근거 한 건입니다."""
    source: str  # 원본 파일명입니다.
    page: int | None = None  # PDF 페이지 번호이며 일반 텍스트는 None입니다.
    chunk_id: int  # 문서 조각 번호입니다.
    score: float  # 검색 점수입니다.
    preview: str  # 화면에 표시할 근거 미리보기입니다.

class AskResponse(BaseModel):
    """텍스트 질문과 음성 질문의 공통 응답입니다."""
    question: str  # STT 이후 최종 질문 문자열입니다.
    answer: str  # 고객에게 전달할 답변입니다.
    sources: list[SourceItem]  # 답변 근거 문서 목록입니다.
    audio_url: str | None  # 생성된 TTS 파일 URL입니다.
    model_mode: str  # 현재 답변 생성 모드입니다.
