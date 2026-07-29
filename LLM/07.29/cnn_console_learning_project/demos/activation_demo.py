"""
ReLU 활성화 함수의 순전파와 역전파 원리를 확인하는 모듈입니다.
"""

# 배열 기반 수치 연산을 수행하기 위해 NumPy를 가져옵니다.
import numpy as np


def relu(values: np.ndarray) -> np.ndarray:
    """
    입력 배열의 음수 값을 0으로 바꾸고 양수 값을 유지합니다.
    """

    # 입력값과 0을 원소별로 비교하여 더 큰 값을 선택합니다.
    return np.maximum(0, values)


def relu_gradient(values: np.ndarray) -> np.ndarray:
    """
    ReLU의 입력값에 대한 미분값을 계산합니다.
    """

    # 입력이 0보다 큰 위치에는 1을, 나머지 위치에는 0을 배치합니다.
    return (values > 0).astype(np.float64)


def run_activation_demo() -> None:
    """
    ReLU의 출력값과 역전파 기울기를 함께 출력합니다.
    """

    # 실습 제목을 출력합니다.
    print("\n[4. ReLU 활성화 함수 연산]")

    # 음수, 0, 양수를 포함하는 입력 배열을 생성합니다.
    values = np.array([-3.0, -1.0, 0.0, 2.0, 5.0])

    # ReLU 함수를 적용한 출력값을 계산합니다.
    activated = relu(values)

    # ReLU의 각 입력 위치에 대한 기울기를 계산합니다.
    gradients = relu_gradient(values)

    # 원본 입력값을 출력합니다.
    print("\n입력값:")

    # 입력 배열을 출력합니다.
    print(values)

    # ReLU 적용 결과를 출력합니다.
    print("\nReLU 출력:")

    # 활성화된 값을 출력합니다.
    print(activated)

    # ReLU 역전파에 사용되는 기울기를 출력합니다.
    print("\nReLU 미분값:")

    # 각 입력 위치에 대한 미분값을 출력합니다.
    print(gradients)

    # ReLU의 동작 원리를 설명합니다.
    print("\n입력이 양수이면 값과 기울기가 전달됩니다.")

    # 음수 및 0 입력의 동작 원리를 설명합니다.
    print("입력이 0 이하이면 출력과 기울기가 0이 됩니다.")
