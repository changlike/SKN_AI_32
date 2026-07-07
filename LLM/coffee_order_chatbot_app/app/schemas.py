# FastAPI 요청과 응답 데이터 구조를 정의하기 위해 Pydantic을 불러옵니다.
from pydantic import BaseModel, Field


# 사용자가 챗봇에 보내는 요청 데이터 구조입니다.
class ChatRequest(BaseModel):
    # 사용자가 입력한 자연어 메시지입니다.
    message: str = Field(..., min_length=1, description="사용자 입력 메시지")
    # 사용자가 선택한 추천 메뉴 개수입니다.
    top_k: int = Field(default=3, ge=1, le=5, description="추천 메뉴 개수")


# 장바구니에 담을 때 사용하는 요청 데이터 구조입니다.
class CartAddRequest(BaseModel):
    # 메뉴 고유 번호입니다.
    menu_id: int = Field(..., description="메뉴 ID")
    # hot 또는 ice 온도 옵션입니다.
    temperature: str = Field(default="ice", description="온도 옵션")
    # 주문 수량입니다.
    quantity: int = Field(default=1, ge=1, le=20, description="수량")
    # 샷 추가, 시럽 추가 등 사용자 요청사항입니다.
    option_note: str = Field(default="", description="추가 옵션")
