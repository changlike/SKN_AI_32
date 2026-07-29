"""
RGB 형태의 다중 채널 입력에 대한 합성곱 연산을 설명하는 모듈입니다.
"""

# 다차원 배열 계산을 위해 NumPy를 가져옵니다.
import numpy as np


def multichannel_convolution_at_one_position(
    input_tensor: np.ndarray,
    kernel: np.ndarray,
    bias: float = 0.0,
) -> float:
    """
    하나의 공간 위치에서 다중 채널 합성곱 값을 계산합니다.
    """

    # 입력과 커널의 형태가 다른 경우 원소별 곱셈이 불가능하므로 예외를 발생시킵니다.
    if input_tensor.shape != kernel.shape:
        # 입력과 커널의 모양이 같아야 한다는 예외 메시지를 생성합니다.
        raise ValueError("입력 영역과 커널의 모양은 같아야 합니다.")

    # 입력과 커널을 원소별로 곱합니다.
    multiplied = input_tensor * kernel

    # 모든 채널과 공간 위치의 곱셈 결과를 더한 후 편향을 추가합니다.
    result = float(np.sum(multiplied) + bias)

    # 최종 합성곱 결과를 반환합니다.
    return result


def run_multichannel_demo() -> None:
    """
    2×2×3 RGB 입력 영역과 같은 크기의 커널을 사용하여 연산합니다.
    """

    # 실습 제목을 출력합니다.
    print("\n[6. 다중 채널 합성곱 연산]")

    # 3개 채널을 가진 2×2 입력 영역을 생성합니다.
    input_tensor = np.array(
        [
            [
                [1, 2],
                [3, 4],
            ],
            [
                [2, 1],
                [0, 1],
            ],
            [
                [1, 0],
                [2, 1],
            ],
        ],
        dtype=np.float64,
    )

    # 입력의 각 채널에 적용할 2×2×3 커널을 생성합니다.
    kernel = np.array(
        [
            [
                [1, 0],
                [0, -1],
            ],
            [
                [0, 1],
                [1, 0],
            ],
            [
                [1, 1],
                [0, 0],
            ],
        ],
        dtype=np.float64,
    )

    # 필터에 더할 편향 값을 설정합니다.
    bias = 0.5

    # 다중 채널 합성곱 결과를 계산합니다.
    result = multichannel_convolution_at_one_position(
        input_tensor=input_tensor,
        kernel=kernel,
        bias=bias,
    )

    # 입력 텐서의 형태를 출력합니다.
    print(f"\n입력 형태: {input_tensor.shape} = 채널×높이×너비")

    # 커널의 형태를 출력합니다.
    print(f"커널 형태: {kernel.shape} = 채널×높이×너비")

    # 각 채널의 입력과 커널 및 계산 결과를 순서대로 출력합니다.
    for channel_index in range(input_tensor.shape[0]):
        # 현재 채널 번호를 출력합니다.
        print(f"\n채널 {channel_index + 1} 입력:")

        # 현재 채널의 입력 행렬을 출력합니다.
        print(input_tensor[channel_index])

        # 현재 채널의 커널을 출력합니다.
        print(f"채널 {channel_index + 1} 커널:")

        # 현재 채널의 커널 행렬을 출력합니다.
        print(kernel[channel_index])

        # 현재 채널의 원소별 곱셈 결과를 출력합니다.
        print(f"채널 {channel_index + 1} 원소별 곱:")

        # 현재 채널의 입력과 커널을 원소별로 곱한 결과를 출력합니다.
        print(input_tensor[channel_index] * kernel[channel_index])

        # 현재 채널의 곱셈 결과 합계를 출력합니다.
        print(
            "채널 합계:",
            np.sum(input_tensor[channel_index] * kernel[channel_index]),
        )

    # 모든 채널의 결과와 편향을 더한 최종 값을 출력합니다.
    print(f"\n모든 채널의 합 + 편향({bias}) = {result}")

    # 필터 하나가 출력 채널 하나를 생성한다는 점을 설명합니다.
    print("필터 하나는 하나의 출력 특성 맵을 생성합니다.")
