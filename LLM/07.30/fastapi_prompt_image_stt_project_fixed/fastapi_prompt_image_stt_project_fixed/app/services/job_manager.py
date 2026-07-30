"""백그라운드 이미지 생성 작업 상태를 메모리에서 관리합니다."""

# 동시 접근 충돌을 막기 위해 Lock을 가져옵니다.
from threading import Lock

# 다양한 상태 값 타입을 허용하기 위해 Any를 가져옵니다.
from typing import Any


# 작업 상태 관리 클래스를 정의합니다.
class JobManager:
    """작업 ID별 진행률, 중간 이미지, 결과와 오류를 관리합니다."""

    def __init__(self) -> None:
        # 작업 상태를 보관할 딕셔너리를 생성합니다.
        self._jobs: dict[str, dict[str, Any]] = {}

        # 여러 스레드의 상태 접근을 보호할 잠금 객체를 생성합니다.
        self._lock = Lock()

    def create(self, job_id: str, initial_data: dict[str, Any]) -> None:
        """새로운 작업 상태를 등록합니다."""

        # 잠금 구역에서 상태를 안전하게 저장합니다.
        with self._lock:
            self._jobs[job_id] = dict(initial_data)

    def update(self, job_id: str, **changes: Any) -> None:
        """기존 작업 상태의 일부 필드를 갱신합니다."""

        # 잠금 구역에서 상태를 안전하게 변경합니다.
        with self._lock:
            # 작업 ID가 존재하는지 확인합니다.
            if job_id not in self._jobs:
                # 존재하지 않으면 명확한 오류를 발생시킵니다.
                raise KeyError(f"존재하지 않는 작업 ID입니다: {job_id}")

            # 전달받은 변경 내용을 기존 상태에 반영합니다.
            self._jobs[job_id].update(changes)

    def get(self, job_id: str) -> dict[str, Any] | None:
        """작업 상태의 복사본을 반환합니다."""

        # 잠금 구역에서 상태를 안전하게 읽습니다.
        with self._lock:
            # 작업이 없으면 None을 반환합니다.
            if job_id not in self._jobs:
                return None

            # 외부 수정 방지를 위해 복사본을 반환합니다.
            return dict(self._jobs[job_id])


# 애플리케이션 전체에서 공유할 작업 관리자 객체를 생성합니다.
job_manager = JobManager()
