"""
NumPy를 사용하여 2차원 합성곱 연산을 직접 구현하는 모듈입니다.
"""

# 수치 행렬 연산을 수행하기 위해 NumPy를 가져옵니다.
import numpy as np


def convolution_2d(
    input_matrix: np.ndarray,
    kernel: np.ndarray,
    stride: int = 1,
    padding: int = 0,
) -> np.ndarray:
    """
    단일 채널 2차원 입력에 커널을 적용하여 특성 맵을 계산합니다.

    Args:
        input_matrix: 높이와 너비를 가진 2차원 입력 행렬입니다.
        kernel: 합성곱에 사용할 2차원 커널입니다.
        stride: 커널이 한 번에 이동하는 칸 수입니다.
        padding: 입력 가장자리에 추가할 0의 두께입니다.

    Returns:
        합성곱 연산으로 생성된 2차원 특성 맵입니다.
    """

    # 스트라이드가 1보다 작은 경우 잘못된 입력이므로 예외를 발생시킵니다.
    if stride < 1:
        # 잘못된 스트라이드 값에 대한 설명을 포함한 예외를 발생시킵니다.
        raise ValueError("stride는 1 이상의 정수여야 합니다.")

    # 패딩이 음수인 경우 잘못된 입력이므로 예외를 발생시킵니다.
    if padding < 0:
        # 잘못된 패딩 값에 대한 설명을 포함한 예외를 발생시킵니다.
        raise ValueError("padding은 0 이상의 정수여야 합니다.")

    # 입력 행렬의 가장자리에 지정된 두께만큼 0을 추가합니다.
    padded_input = np.pad(
        input_matrix,
        pad_width=padding,
        mode="constant",
        constant_values=0,
    )

    # 패딩이 적용된 입력 행렬의 높이를 가져옵니다.
    input_height = padded_input.shape[0]

    # 패딩이 적용된 입력 행렬의 너비를 가져옵니다.
    input_width = padded_input.shape[1]

    # 커널의 높이를 가져옵니다.
    kernel_height = kernel.shape[0]

    # 커널의 너비를 가져옵니다.
    kernel_width = kernel.shape[1]

    # 출력 특성 맵의 높이를 계산합니다.
    output_height = ((input_height - kernel_height) // stride) + 1

    # 출력 특성 맵의 너비를 계산합니다.
    output_width = ((input_width - kernel_width) // stride) + 1

    # 출력 높이나 너비가 1보다 작은 경우 커널이 입력보다 큰 상황이므로 예외를 발생시킵니다.
    if output_height < 1 or output_width < 1:
        # 입력과 커널의 크기 관계가 올바르지 않음을 알리는 예외를 발생시킵니다.
        raise ValueError("커널 크기가 패딩이 적용된 입력 크기보다 큽니다.")

    # 계산 결과를 저장할 0으로 초기화된 출력 배열을 생성합니다.
    output = np.zeros((output_height, output_width), dtype=np.float64)

    # 출력 특성 맵의 각 행 위치를 순서대로 반복합니다.
    for output_row in range(output_height):
        # 현재 출력 행에 대응하는 입력 시작 행을 계산합니다.
        input_row_start = output_row * stride

        # 출력 특성 맵의 각 열 위치를 순서대로 반복합니다.
        for output_col in range(output_width):
            # 현재 출력 열에 대응하는 입력 시작 열을 계산합니다.
            input_col_start = output_col * stride

            # 현재 커널이 덮는 입력 영역을 추출합니다.
            region = padded_input[
                input_row_start:input_row_start + kernel_height,
                input_col_start:input_col_start + kernel_width,
            ]

            # 입력 영역과 커널을 같은 위치끼리 곱한 후 모두 더합니다.
            result = np.sum(region * kernel)

            # 계산한 값을 출력 특성 맵의 현재 위치에 저장합니다.
            output[output_row, output_col] = result

            # 현재 계산 위치와 선택된 입력 영역을 출력합니다.
            print(
                f"\n출력 위치 ({output_row}, {output_col})에 대응하는 입력 영역:"
            )

            # 현재 선택된 입력 영역을 출력합니다.
            print(region)

            # 사용한 커널을 출력합니다.
            print("커널:")

            # 커널 행렬을 출력합니다.
            print(kernel)

            # 원소별 곱셈 결과를 출력합니다.
            print("원소별 곱셈 결과:")

            # 입력 영역과 커널의 원소별 곱셈 결과를 출력합니다.
            print(region * kernel)

            # 현재 위치의 최종 합성곱 결과를 출력합니다.
            print(f"합계: {result}")

    # 모든 위치의 합성곱 계산이 완료된 출력 특성 맵을 반환합니다.
    return output


def run_convolution_demo() -> None:
    """
    4×4 입력과 2×2 커널을 사용하여 합성곱 계산 과정을 확인합니다.
    """

    # 실습 제목을 출력합니다.
    print("\n[2. NumPy 기반 2차원 합성곱 연산]")

    # 합성곱에 사용할 4×4 입력 행렬을 생성합니다.
    input_matrix = np.array(
        [
            [1, 2, 0, 1],
            [3, 1, 2, 2],
            [0, 1, 3, 1],
            [2, 2, 1, 0],
        ],
        dtype=np.float64,
    )

    # 입력에서 대각선 방향의 차이를 계산하는 2×2 커널을 생성합니다.
    kernel = np.array(
        [
            [1, 0],
            [0, -1],
        ],
        dtype=np.float64,
    )

    # 합성곱 연산에 사용할 스트라이드를 1로 설정합니다.
    stride = 1

    # 입력 가장자리에 추가할 패딩을 0으로 설정합니다.
    padding = 0

    # 실습에 사용되는 입력 행렬을 출력합니다.
    print("\n입력 행렬:")

    # 입력 행렬의 값을 출력합니다.
    print(input_matrix)

    # 실습에 사용되는 커널을 출력합니다.
    print("\n커널:")

    # 커널의 값을 출력합니다.
    print(kernel)

    # 직접 구현한 합성곱 함수를 호출하여 출력 특성 맵을 계산합니다.
    output = convolution_2d(
        input_matrix=input_matrix,
        kernel=kernel,
        stride=stride,
        padding=padding,
    )

    # 최종 결과를 구분하기 위한 제목을 출력합니다.
    print("\n최종 출력 특성 맵:")

    # 합성곱 연산으로 생성된 특성 맵을 출력합니다.
    print(output)
