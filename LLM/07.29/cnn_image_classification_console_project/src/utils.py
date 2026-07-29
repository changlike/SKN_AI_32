"""난수 시드, 장치 선택, 환경 출력, CSV 저장 기능을 제공합니다."""

# CSV 파일 저장을 위해 csv 모듈을 가져옵니다.
import csv

# Python 난수 시드를 설정하기 위해 random 모듈을 가져옵니다.
import random

# Python 버전 정보를 출력하기 위해 sys 모듈을 가져옵니다.
import sys

# 파일 경로 타입을 사용하기 위해 Path를 가져옵니다.
from pathlib import Path

# NumPy 난수 시드를 설정하기 위해 NumPy를 가져옵니다.
import numpy as np

# 텐서 연산과 CUDA 확인을 위해 PyTorch를 가져옵니다.
import torch


def set_seed(seed: int) -> None:
    """Python, NumPy, PyTorch의 난수 시드를 고정합니다."""

    # Python 표준 난수 생성기의 시드를 설정합니다.
    random.seed(seed)

    # NumPy 난수 생성기의 시드를 설정합니다.
    np.random.seed(seed)

    # CPU에서 사용하는 PyTorch 난수 시드를 설정합니다.
    torch.manual_seed(seed)

    # 모든 CUDA 장치의 PyTorch 난수 시드를 설정합니다.
    torch.cuda.manual_seed_all(seed)

    # 가능한 범위에서 CuDNN이 결정론적 알고리즘을 사용하도록 설정합니다.
    torch.backends.cudnn.deterministic = True

    # 입력에 따라 알고리즘을 바꾸는 벤치마크 기능을 비활성화합니다.
    torch.backends.cudnn.benchmark = False


def get_device() -> torch.device:
    """CUDA GPU가 있으면 GPU를, 없으면 CPU를 반환합니다."""

    # CUDA 사용 가능 여부에 따라 장치 이름을 선택합니다.
    device_name = "cuda" if torch.cuda.is_available() else "cpu"

    # 문자열 장치 이름을 PyTorch 장치 객체로 변환합니다.
    return torch.device(device_name)


def print_environment() -> None:
    """현재 Python, PyTorch, CUDA 실행 환경을 출력합니다."""

    # 환경 정보 제목을 출력합니다.
    print("\n[실행 환경]")

    # 현재 Python 버전을 출력합니다.
    print(f"Python: {sys.version.split()[0]}")

    # 현재 PyTorch 버전을 출력합니다.
    print(f"PyTorch: {torch.__version__}")

    # CUDA 사용 가능 여부를 출력합니다.
    print(f"CUDA 사용 가능: {torch.cuda.is_available()}")

    # 실제 선택되는 장치를 출력합니다.
    print(f"선택 장치: {get_device()}")

    # CUDA GPU를 사용할 수 있는 경우 GPU 이름을 출력합니다.
    if torch.cuda.is_available():
        # 첫 번째 GPU 장치 이름을 출력합니다.
        print(f"GPU: {torch.cuda.get_device_name(0)}")


def save_history(history: list[dict], path: Path) -> None:
    """에포크별 학습 이력을 CSV 파일로 저장합니다."""

    # 저장할 이력이 없으면 파일 생성을 생략합니다.
    if not history:
        # 현재 함수를 즉시 종료합니다.
        return

    # CSV 파일의 상위 폴더가 없으면 생성합니다.
    path.parent.mkdir(parents=True, exist_ok=True)

    # 한글 호환을 위해 UTF-8 BOM을 포함한 쓰기 모드로 파일을 엽니다.
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        # 첫 번째 이력 사전의 키를 열 이름으로 사용하는 작성기를 생성합니다.
        writer = csv.DictWriter(file, fieldnames=history[0].keys())

        # CSV의 첫 행에 열 이름을 기록합니다.
        writer.writeheader()

        # 모든 에포크 이력을 행 단위로 기록합니다.
        writer.writerows(history)
