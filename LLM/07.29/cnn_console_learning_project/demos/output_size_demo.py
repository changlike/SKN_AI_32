"""
스트라이드와 패딩에 따른 합성곱 출력 크기를 계산하는 모듈입니다.
"""

# 내림 연산이 포함된 수학 계산을 수행하기 위해 math 모듈을 가져옵니다.
import math


def calculate_output_size(
    input_size: int,
    kernel_size: int,
    stride: int,
    padding: int,
) -> int:
    """
    1차원 기준 합성곱 출력 크기를 계산합니다.

    공식:
        floor((입력 크기 - 커널 크기 + 2 × 패딩) / 스트라이드) + 1
    """

    # 입력 크기가 1보다 작은 경우 계산할 수 없으므로 예외를 발생시킵니다.
    if input_size < 1:
        # 입력 크기 조건을 설명하는 예외를 발생시킵니다.
        raise ValueError("input_size는 1 이상이어야 합니다.")

    # 커널 크기가 1보다 작은 경우 계산할 수 없으므로 예외를 발생시킵니다.
    if kernel_size < 1:
        # 커널 크기 조건을 설명하는 예외를 발생시킵니다.
        raise ValueError("kernel_size는 1 이상이어야 합니다.")

    # 스트라이드가 1보다 작은 경우 계산할 수 없으므로 예외를 발생시킵니다.
    if stride < 1:
        # 스트라이드 조건을 설명하는 예외를 발생시킵니다.
        raise ValueError("stride는 1 이상이어야 합니다.")

    # 패딩이 음수인 경우 계산할 수 없으므로 예외를 발생시킵니다.
    if padding < 0:
        # 패딩 조건을 설명하는 예외를 발생시킵니다.
        raise ValueError("padding은 0 이상이어야 합니다.")

    # 출력 크기 계산식의 분자를 계산합니다.
    numerator = input_size - kernel_size + (2 * padding)

    # 커널을 적용할 수 없는 경우 예외를 발생시킵니다.
    if numerator < 0:
        # 입력보다 커널이 지나치게 크다는 설명을 포함한 예외를 발생시킵니다.
        raise ValueError("패딩이 적용된 입력 크기보다 커널 크기가 큽니다.")

    # 공식에 따라 출력 크기를 계산하고 내림 처리합니다.
    output_size = math.floor(numerator / stride) + 1

    # 계산한 출력 크기를 반환합니다.
    return output_size


def run_output_size_demo() -> None:
    """
    여러 스트라이드와 패딩 설정에 따른 출력 크기를 비교합니다.
    """

    # 실습 제목을 출력합니다.
    print("\n[3. 스트라이드와 패딩에 따른 출력 크기 비교]")

    # 비교에 사용할 설정 목록을 정의합니다.
    cases = [
        {
            "name": "Valid 합성곱",
            "input_size": 5,
            "kernel_size": 3,
            "stride": 1,
            "padding": 0,
        },
        {
            "name": "Same 크기 유지",
            "input_size": 5,
            "kernel_size": 3,
            "stride": 1,
            "padding": 1,
        },
        {
            "name": "스트라이드 2",
            "input_size": 5,
            "kernel_size": 3,
            "stride": 2,
            "padding": 0,
        },
        {
            "name": "32×32 입력 크기 유지",
            "input_size": 32,
            "kernel_size": 3,
            "stride": 1,
            "padding": 1,
        },
    ]

    # 출력 크기 계산 공식을 콘솔에 출력합니다.
    print(
        "\n출력 크기 = floor((입력 - 커널 + 2×패딩) / 스트라이드) + 1"
    )

    # 준비한 각 설정을 순서대로 반복합니다.
    for case in cases:
        # 현재 설정에 따른 출력 크기를 계산합니다.
        output_size = calculate_output_size(
            input_size=case["input_size"],
            kernel_size=case["kernel_size"],
            stride=case["stride"],
            padding=case["padding"],
        )

        # 현재 설정의 이름을 출력합니다.
        print(f"\n[{case['name']}]")

        # 입력 크기를 출력합니다.
        print(f"입력 크기: {case['input_size']}")

        # 커널 크기를 출력합니다.
        print(f"커널 크기: {case['kernel_size']}")

        # 스트라이드 값을 출력합니다.
        print(f"스트라이드: {case['stride']}")

        # 패딩 값을 출력합니다.
        print(f"패딩: {case['padding']}")

        # 최종 출력 크기를 출력합니다.
        print(f"출력 크기: {output_size}")
