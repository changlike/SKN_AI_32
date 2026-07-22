# -*- coding: utf-8 -*-
"""'교환해 주세요', '환불해 주세요' 같은 실행 질문을 감지해 담당 부서 접수 메시지를 저장하는 서비스입니다."""

# datetime은 문의 접수 시각을 기록합니다.
from datetime import datetime

# MySQL 커넥션 함수를 가져옵니다.
from app.core.db import get_connection
from app.core.logging_config import setup_logging

# 공용 로거를 모듈 로드 시 한 번 초기화합니다.
logger = setup_logging()

# _DEPARTMENT_RULES는 (부서 판단용 키워드 목록, dept_id) 순서쌍입니다.
# 위에서부터 먼저 매칭되는 규칙이 우선 적용됩니다.
_DEPARTMENT_RULES: list[tuple[list[str], str]] = [
    (["교환해 주세요", "교환해주세요", "교환 해주세요", "교환 요청"], "EXCHANGE_TEAM"),
    (["환불해 주세요", "환불해주세요", "환불 해주세요", "환불 요청"], "REFUND_TEAM"),
]

# 고정 응답 문구입니다. 실행 질문이 감지되면 항상 이 문장으로 답합니다.
FIXED_ANSWER = "담당 부서로 연결해 드리겠습니다."


# detect_department 함수는 문의 내용에서 실행 질문 여부와 담당 부서를 판단합니다.
def detect_department(message: str) -> str | None:
    """메시지가 실행 질문이면 dept_id를, 아니면 None을 반환합니다."""
    # 문의 내용의 앞뒤 공백을 제거합니다.
    normalized = message.strip()
    # 등록된 규칙을 순서대로 검사합니다.
    for keywords, dept_id in _DEPARTMENT_RULES:
        # 키워드 중 하나라도 포함되면 해당 부서로 판단합니다.
        if any(keyword in normalized for keyword in keywords):
            # 매칭된 부서 ID를 반환합니다.
            return dept_id
    # 어떤 실행 질문 키워드와도 일치하지 않으면 None을 반환합니다.
    return None


# _insert_complaint 함수는 customer_complaint 테이블에 신규 문의를 저장합니다.
def _insert_complaint(customer_id: str, dept_id: str, message: str) -> int:
    """새 접수 건을 INSERT하고 생성된 cc_id를 반환합니다."""
    # 문의 접수 시각을 현재 시간으로 기록합니다.
    inquiry_date = datetime.now()
    # INSERT 문입니다. receipt_status/resolution_status는 최초 접수 시 0(미완료)입니다.
    insert_sql = """
        INSERT INTO customer_complaint
            (custum_id, dept_id, message, receipt_status, resolution_status, inquiry_date)
        VALUES (%s, %s, %s, 0, 0, %s)
    """
    # with 구문으로 커넥션과 커서를 자동으로 닫습니다.
    with get_connection() as conn:
        with conn.cursor() as cursor:
            # 준비된 파라미터로 INSERT를 실행해 SQL 인젝션을 방지합니다.
            cursor.execute(insert_sql, (customer_id, dept_id, message, inquiry_date))
            # 방금 생성된 auto_increment 값을 읽습니다.
            new_id = cursor.lastrowid
        # 변경 사항을 커밋합니다.
        conn.commit()
    # 새로 생성된 cc_id를 반환합니다.
    return new_id


# handle_customer_inquiry 함수는 문의 처리 탭 API가 호출하는 진입점입니다.
def handle_customer_inquiry(customer_id: str, message: str) -> dict[str, object]:
    """실행 질문이면 DB에 접수하고 고정 응답을, 아니면 안내 응답을 반환합니다."""
    # 메시지에서 담당 부서를 판단합니다.
    dept_id = detect_department(message)
    # 실행 질문이 아니면 접수 없이 안내만 반환합니다.
    if dept_id is None:
        # 로그에 미매칭 사실을 남깁니다.
        logger.info("실행 질문 미감지: customer_id=%s", customer_id)
        # matched=False로 접수되지 않았음을 알립니다.
        return {
            "matched": False,
            "answer": "교환/환불처럼 처리가 필요한 요청이 감지되지 않아 접수하지 않았습니다.",
            "dept_id": None,
            "cc_id": None,
        }
    # 실제 DB INSERT를 수행합니다.
    cc_id = _insert_complaint(customer_id, dept_id, message)
    # 접수 성공을 구조적 로그로 남깁니다.
    logger.info("고객 문의 접수 완료: cc_id=%s customer_id=%s dept_id=%s", cc_id, customer_id, dept_id)
    # 고정 응답과 접수 결과를 함께 반환합니다.
    return {"matched": True, "answer": FIXED_ANSWER, "dept_id": dept_id, "cc_id": cc_id}
