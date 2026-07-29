"""
합성곱 계층과 완전연결 계층의 파라미터 수를 계산하는 모듈입니다.
"""


def calculate_conv_parameters(
    kernel_height: int,
    kernel_width: int,
    input_channels: int,
    output_channels: int,
    use_bias: bool = True,
) -> int:
    """
    합성곱 계층의 학습 파라미터 수를 계산합니다.
    """

    # 필터 한 개에 포함된 가중치 수를 계산합니다.
    weights_per_filter = kernel_height * kernel_width * input_channels

    # 편향을 사용하는 경우 필터 한 개당 편향 1개를 추가합니다.
    bias_per_filter = 1 if use_bias else 0

    # 필터 한 개의 파라미터 수에 출력 필터 수를 곱합니다.
    total_parameters = (
        weights_per_filter + bias_per_filter
    ) * output_channels

    # 최종 파라미터 수를 반환합니다.
    return total_parameters


def calculate_linear_parameters(
    input_features: int,
    output_features: int,
    use_bias: bool = True,
) -> int:
    """
    완전연결 계층의 학습 파라미터 수를 계산합니다.
    """

    # 입력 특징과 출력 특징 사이의 모든 연결 가중치 수를 계산합니다.
    weight_parameters = input_features * output_features

    # 편향을 사용하는 경우 출력 뉴런 수만큼 편향을 추가합니다.
    bias_parameters = output_features if use_bias else 0

    # 가중치와 편향을 더하여 전체 파라미터 수를 계산합니다.
    total_parameters = weight_parameters + bias_parameters

    # 최종 파라미터 수를 반환합니다.
    return total_parameters


def run_parameter_demo() -> None:
    """
    대표적인 합성곱 계층과 완전연결 계층의 파라미터 수를 비교합니다.
    """

    # 실습 제목을 출력합니다.
    print("\n[8. 합성곱 계층의 파라미터 수 계산]")

    # 3×3 커널, 입력 채널 3개, 출력 채널 64개의 합성곱 파라미터를 계산합니다.
    conv_parameters = calculate_conv_parameters(
        kernel_height=3,
        kernel_width=3,
        input_channels=3,
        output_channels=64,
        use_bias=True,
    )

    # 합성곱 계층의 계산 공식을 출력합니다.
    print("\n합성곱 파라미터 공식:")

    # 공식의 의미를 문자열로 출력합니다.
    print("(커널 높이 × 커널 너비 × 입력 채널 + 편향 1) × 출력 채널")

    # 현재 예제의 계산식을 출력합니다.
    print("(3 × 3 × 3 + 1) × 64")

    # 합성곱 계층의 최종 파라미터 수를 출력합니다.
    print(f"합성곱 파라미터 수: {conv_parameters:,}")

    # 150,528개 입력 특징과 1,000개 출력 뉴런의 완전연결 파라미터를 계산합니다.
    linear_parameters = calculate_linear_parameters(
        input_features=150_528,
        output_features=1_000,
        use_bias=True,
    )

    # 완전연결 계층의 계산 공식을 출력합니다.
    print("\n완전연결 파라미터 공식:")

    # 완전연결 계층의 공식 의미를 출력합니다.
    print("입력 특징 × 출력 특징 + 출력 편향")

    # 현재 예제의 계산식을 출력합니다.
    print("150,528 × 1,000 + 1,000")

    # 완전연결 계층의 최종 파라미터 수를 출력합니다.
    print(f"완전연결 파라미터 수: {linear_parameters:,}")

    # 두 계층의 파라미터 차이를 설명합니다.
    print("\nCNN은 작은 커널을 공유하므로 이미지 전체를 완전연결하는 방식보다")

    # 가중치 공유의 장점을 이어서 설명합니다.
    print("훨씬 적은 파라미터로 공간 특징을 추출할 수 있습니다.")
