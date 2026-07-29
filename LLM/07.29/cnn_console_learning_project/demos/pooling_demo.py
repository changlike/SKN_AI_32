"""
최대 풀링과 평균 풀링을 직접 구현하여 비교하는 모듈입니다.
"""

# 수치 행렬 연산을 수행하기 위해 NumPy를 가져옵니다.
import numpy as np


def pool_2d(
    input_matrix: np.ndarray,
    pool_size: int = 2,
    stride: int = 2,
    mode: str = "max",
) -> np.ndarray:
    """
    2차원 입력 행렬에 최대 풀링 또는 평균 풀링을 적용합니다.
    """

    # 지원하는 풀링 방식인지 확인합니다.
    if mode not in {"max", "average"}:
        # 지원하지 않는 방식이 입력되면 예외를 발생시킵니다.
        raise ValueError("mode는 'max' 또는 'average'여야 합니다.")

    # 입력 행렬의 높이를 가져옵니다.
    input_height = input_matrix.shape[0]

    # 입력 행렬의 너비를 가져옵니다.
    input_width = input_matrix.shape[1]

    # 풀링 출력의 높이를 계산합니다.
    output_height = ((input_height - pool_size) // stride) + 1

    # 풀링 출력의 너비를 계산합니다.
    output_width = ((input_width - pool_size) // stride) + 1

    # 풀링 결과를 저장할 배열을 0으로 초기화합니다.
    output = np.zeros((output_height, output_width), dtype=np.float64)

    # 출력의 각 행 위치를 순서대로 반복합니다.
    for output_row in range(output_height):
        # 현재 출력 행에 대응하는 입력 시작 행을 계산합니다.
        input_row_start = output_row * stride

        # 출력의 각 열 위치를 순서대로 반복합니다.
        for output_col in range(output_width):
            # 현재 출력 열에 대응하는 입력 시작 열을 계산합니다.
            input_col_start = output_col * stride

            # 현재 풀링 창이 덮는 입력 영역을 추출합니다.
            region = input_matrix[
                input_row_start:input_row_start + pool_size,
                input_col_start:input_col_start + pool_size,
            ]

            # 최대 풀링 모드인 경우 영역의 최댓값을 계산합니다.
            if mode == "max":
                # 현재 영역의 최댓값을 출력 배열에 저장합니다.
                output[output_row, output_col] = np.max(region)

            # 평균 풀링 모드인 경우 영역의 평균값을 계산합니다.
            else:
                # 현재 영역의 평균값을 출력 배열에 저장합니다.
                output[output_row, output_col] = np.mean(region)

    # 계산이 완료된 풀링 결과를 반환합니다.
    return output


def run_pooling_demo() -> None:
    """
    같은 입력에 최대 풀링과 평균 풀링을 적용하여 차이를 확인합니다.
    """

    # 실습 제목을 출력합니다.
    print("\n[5. 최대 풀링과 평균 풀링 연산]")

    # 풀링 실습에 사용할 4×4 입력 행렬을 생성합니다.
    input_matrix = np.array(
        [
            [1, 3, 2, 0],
            [4, 6, 1, 2],
            [2, 1, 5, 3],
            [0, 2, 4, 8],
        ],
        dtype=np.float64,
    )

    # 2×2 최대 풀링을 스트라이드 2로 적용합니다.
    max_output = pool_2d(
        input_matrix=input_matrix,
        pool_size=2,
        stride=2,
        mode="max",
    )

    # 2×2 평균 풀링을 스트라이드 2로 적용합니다.
    average_output = pool_2d(
        input_matrix=input_matrix,
        pool_size=2,
        stride=2,
        mode="average",
    )

    # 원본 입력 행렬을 출력합니다.
    print("\n입력 특성 맵:")

    # 입력 행렬의 값을 출력합니다.
    print(input_matrix)

    # 최대 풀링 결과를 출력합니다.
    print("\n2×2 최대 풀링 결과:")

    # 최대 풀링 출력 배열을 출력합니다.
    print(max_output)

    # 평균 풀링 결과를 출력합니다.
    print("\n2×2 평균 풀링 결과:")

    # 평균 풀링 출력 배열을 출력합니다.
    print(average_output)

    # 두 풀링 방식의 차이를 설명합니다.
    print("\n최대 풀링은 가장 강한 특징을 유지합니다.")

    # 평균 풀링의 의미를 설명합니다.
    print("평균 풀링은 영역 전체의 정보를 평균으로 요약합니다.")
