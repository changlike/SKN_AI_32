# -*- coding: utf-8 -*-
"""최종 답변을 MySQL REPORT 테이블에 저장하는 서비스입니다."""

# 저장 시각을 기록하기 위해 datetime을 가져옵니다.
import datetime
# 접속 정보를 환경변수에서 읽기 위해 os를 가져옵니다.
import os

# .env가 로드되도록 공통 모듈을 가져옵니다.
from app.core.common import require_key


def _connect():
    """환경변수의 접속 정보로 MySQL 커넥션을 생성합니다."""
    # 지연 임포트로 MySQL 미설치 환경에서도 앱 시작을 막지 않습니다.
    import pymysql

    # 필수 접속 정보가 비어 있으면 명확한 오류를 냅니다.
    password = require_key("MYSQL_PASSWORD")
    # 나머지 접속 정보와 함께 커넥션을 생성합니다.
    return pymysql.connect(
        host=os.getenv("MYSQL_HOST", "127.0.0.1"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        user=os.getenv("MYSQL_USER", "root"),
        password=password,
        database=os.getenv("MYSQL_DATABASE", "research_agent"),
        charset="utf8mb4",
        autocommit=True,
    )


def _ensure_table(connection) -> None:
    """REPORT 테이블이 없으면 생성합니다."""
    with connection.cursor() as cursor:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS REPORT (
                ID INT AUTO_INCREMENT PRIMARY KEY,
                TOPIC VARCHAR(500) NOT NULL,
                RESULT LONGTEXT NOT NULL,
                RESULT_TIME DATETIME NOT NULL
            ) CHARACTER SET utf8mb4
            """
        )


def save_report_to_db(topic: str, result: str) -> dict[str, object]:
    """최종 답변을 REPORT 테이블에 저장하고 저장 결과를 반환합니다."""
    # 주제와 결과가 비어 있으면 저장을 거부합니다.
    if not topic.strip() or not result.strip():
        raise ValueError("topic과 result는 비어 있을 수 없습니다.")
    # 답변 완료 시각을 기록합니다.
    result_time = datetime.datetime.now()
    # 커넥션을 열고 항상 정리되도록 처리합니다.
    connection = _connect()
    try:
        # 테이블이 없으면 먼저 생성합니다.
        _ensure_table(connection)
        # 새 리포트 행을 삽입합니다.
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO REPORT (TOPIC, RESULT, RESULT_TIME) VALUES (%s, %s, %s)",
                (topic, result, result_time),
            )
            row_id = cursor.lastrowid
        # 저장 확인용 정보를 반환합니다.
        return {"row_id": row_id, "topic": topic, "result_time": result_time.strftime("%Y-%m-%d %H:%M:%S")}
    finally:
        # 성공·실패와 관계없이 커넥션을 닫습니다.
        connection.close()
