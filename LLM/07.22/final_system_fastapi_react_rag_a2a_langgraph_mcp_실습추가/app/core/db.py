# -*- coding: utf-8 -*-
"""fastapi_db(MySQL) 커넥션과 customer_complaint 테이블 초기화를 담당하는 모듈입니다."""

# pymysql은 MySQL과 통신하는 순수 파이썬 드라이버입니다.
import pymysql
# pymysql.cursors의 DictCursor는 조회 결과를 dict 형태로 반환합니다.
from pymysql.cursors import DictCursor

# 공용 환경설정과 로거를 가져옵니다.
from app.core.logging_config import setup_logging
from app.core.settings import get_settings

# 공용 로거를 모듈 로드 시 한 번 초기화합니다.
logger = setup_logging()

# customer_complaint 테이블 생성 DDL입니다. 컬럼 구성은 과제 명세를 그대로 따릅니다.
_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS customer_complaint (
    cc_id INT AUTO_INCREMENT PRIMARY KEY,
    custum_id VARCHAR(50) NOT NULL,
    dept_id VARCHAR(50) NOT NULL,
    message TEXT NOT NULL,
    receipt_status TINYINT(1) NOT NULL DEFAULT 0,
    resolution_status TINYINT(1) NOT NULL DEFAULT 0,
    inquiry_date DATETIME NOT NULL,
    receipt_date DATETIME NULL,
    resolution_date DATETIME NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""


# get_connection 함수는 fastapi_db에 연결된 새 커넥션을 반환합니다.
def get_connection() -> pymysql.connections.Connection:
    """설정값으로 MySQL 커넥션을 생성해 반환합니다."""
    # 환경설정에서 MySQL 접속 정보를 읽습니다.
    settings = get_settings()
    # pymysql.connect는 커넥션 객체를 생성합니다.
    return pymysql.connect(
        host=settings.mysql_host,
        port=settings.mysql_port,
        user=settings.mysql_user,
        password=settings.mysql_password,
        database=settings.mysql_database,
        charset="utf8mb4",
        cursorclass=DictCursor,
        autocommit=False,
    )


# ensure_customer_complaint_table 함수는 앱 시작 시 테이블 존재를 보장합니다.
def ensure_customer_complaint_table() -> None:
    """customer_complaint 테이블이 없으면 생성합니다."""
    # 연결 실패 시 앱 전체가 죽지 않도록 예외를 잡아 로그만 남깁니다.
    try:
        # with 구문으로 커넥션을 열고 자동으로 닫습니다.
        with get_connection() as conn:
            # 커서를 열어 DDL을 실행합니다.
            with conn.cursor() as cursor:
                # 테이블이 없을 때만 생성되는 DDL을 실행합니다.
                cursor.execute(_CREATE_TABLE_SQL)
            # DDL 변경 사항을 커밋합니다.
            conn.commit()
        # 초기화 성공을 로그로 남깁니다.
        logger.info("customer_complaint 테이블 확인 완료")
    except Exception:
        # MySQL이 아직 준비되지 않은 개발 초기 상태를 고려해 경고만 남깁니다.
        logger.exception("customer_complaint 테이블 초기화 실패: MySQL 접속 정보를 확인하세요")
