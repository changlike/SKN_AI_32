"""Django와 동일한 MySQL DB를 읽기 위한 SQLAlchemy 연결 모듈입니다."""
# SQLAlchemy 엔진과 SQL 텍스트 실행 함수를 가져옵니다.
from sqlalchemy import create_engine, text
# 연결 풀 타입 힌트를 위해 Engine 클래스를 가져옵니다.
from sqlalchemy.engine import Engine
# 프로젝트 환경설정을 가져옵니다.
from app.config import settings

# FastAPI 프로세스에서 재사용할 MySQL 연결 엔진을 생성합니다.
engine: Engine = create_engine(
    # .env 정보로 만든 MySQL 연결 문자열을 사용합니다.
    settings.mysql_url,
    # 일정 시간 후 끊긴 MySQL 연결을 사용하기 전에 자동 점검합니다.
    pool_pre_ping=True,
    # Django와 함께 사용할 때 불필요한 연결 급증을 막기 위해 기본 풀 크기를 제한합니다.
    pool_size=5,
    # 순간적으로 허용할 추가 연결 수를 제한합니다.
    max_overflow=5,
    # 필요할 때만 SQL 로그를 출력합니다.
    echo=settings.db_echo,
)


def check_database() -> bool:
    """MySQL 연결 가능 여부를 SELECT 1로 간단히 검사합니다."""
    # with 블록이 끝나면 연결을 자동으로 풀에 반환합니다.
    with engine.connect() as connection:
        # DB 서버에 가장 가벼운 조회를 실행합니다.
        value = connection.execute(text("SELECT 1")).scalar_one()
    # SELECT 1의 결과가 실제로 1인지 반환합니다.
    return value == 1
