"""Django ORM을 FastAPI에 복제하지 않고 기존 게시글 테이블을 읽는 저장소입니다."""
# SQLAlchemy의 안전한 바인딩 SQL 실행 함수를 가져옵니다.
from sqlalchemy import text
# 공용 MySQL 엔진을 가져옵니다.
from app.database import engine


def fetch_all_boards() -> list[dict]:
    """Django boards_board와 members_member를 JOIN하여 RAG 색인용 데이터를 반환합니다."""
    # Django 기본 테이블명을 사용하므로 기존 members/boards 모델 코드는 수정하지 않습니다.
    query = text(
        """
        SELECT
            b.id AS board_id,
            b.title AS title,
            b.content AS content,
            b.created_at AS created_at,
            b.updated_at AS updated_at,
            b.author_id AS author_id,
            COALESCE(m.display_name, m.username, CAST(b.author_id AS CHAR)) AS author_name
        FROM boards_board AS b
        INNER JOIN members_member AS m ON m.id = b.author_id
        ORDER BY b.id DESC
        """
    )
    # DB 연결을 열고 조회한 뒤 자동으로 반환합니다.
    with engine.connect() as connection:
        # mappings()를 사용해 각 행을 컬럼명 기반 딕셔너리처럼 읽습니다.
        rows = connection.execute(query).mappings().all()
    # SQLAlchemy RowMapping을 일반 dict로 변환해 다른 계층과 분리합니다.
    return [dict(row) for row in rows]
