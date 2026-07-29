"""
PyTorch CNN의 순전파 과정과 계층별 텐서 크기를 출력하는 모듈입니다.
"""

# 텐서 생성과 연산을 위해 PyTorch를 가져옵니다.
import torch

# 신경망 계층을 사용하기 위해 torch.nn을 가져옵니다.
import torch.nn as nn


class ShapeTracingCNN(nn.Module):
    """
    각 계층을 통과할 때 텐서 크기를 출력하는 간단한 CNN입니다.
    """

    def __init__(self) -> None:
        """
        CNN에서 사용할 합성곱, 활성화, 풀링, 완전연결 계층을 정의합니다.
        """

        # nn.Module 부모 클래스의 초기화 메서드를 호출합니다.
        super().__init__()

        # 입력 채널 1개를 8개 특징 채널로 변환하는 첫 번째 합성곱을 정의합니다.
        self.conv1 = nn.Conv2d(
            in_channels=1,
            out_channels=8,
            kernel_size=3,
            stride=1,
            padding=1,
        )

        # 비선형성을 추가할 ReLU 계층을 정의합니다.
        self.relu1 = nn.ReLU()

        # 가로와 세로 크기를 절반으로 줄일 최대 풀링 계층을 정의합니다.
        self.pool1 = nn.MaxPool2d(
            kernel_size=2,
            stride=2,
        )

        # 8개 특징 채널을 16개 특징 채널로 변환하는 두 번째 합성곱을 정의합니다.
        self.conv2 = nn.Conv2d(
            in_channels=8,
            out_channels=16,
            kernel_size=3,
            stride=1,
            padding=1,
        )

        # 두 번째 합성곱 뒤에 적용할 ReLU 계층을 정의합니다.
        self.relu2 = nn.ReLU()

        # 공간 크기를 다시 절반으로 줄일 두 번째 최대 풀링 계층을 정의합니다.
        self.pool2 = nn.MaxPool2d(
            kernel_size=2,
            stride=2,
        )

        # 16×7×7 크기의 특징을 32개 은닉 특징으로 변환하는 완전연결 계층을 정의합니다.
        self.fc1 = nn.Linear(
            in_features=16 * 7 * 7,
            out_features=32,
        )

        # 완전연결 계층 뒤에 적용할 ReLU를 정의합니다.
        self.relu3 = nn.ReLU()

        # 32개 은닉 특징을 10개 클래스 로짓으로 변환하는 출력 계층을 정의합니다.
        self.fc2 = nn.Linear(
            in_features=32,
            out_features=10,
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        입력 텐서가 각 계층을 통과하는 과정을 실행하고 크기를 출력합니다.
        """

        # 모델에 처음 전달된 입력 텐서의 크기를 출력합니다.
        print(f"입력                  : {tuple(x.shape)}")

        # 첫 번째 합성곱을 적용합니다.
        x = self.conv1(x)

        # 첫 번째 합성곱 이후 텐서 크기를 출력합니다.
        print(f"첫 번째 합성곱        : {tuple(x.shape)}")

        # 첫 번째 ReLU 활성화 함수를 적용합니다.
        x = self.relu1(x)

        # 첫 번째 ReLU 이후 텐서 크기를 출력합니다.
        print(f"첫 번째 ReLU          : {tuple(x.shape)}")

        # 첫 번째 최대 풀링을 적용합니다.
        x = self.pool1(x)

        # 첫 번째 최대 풀링 이후 텐서 크기를 출력합니다.
        print(f"첫 번째 최대 풀링     : {tuple(x.shape)}")

        # 두 번째 합성곱을 적용합니다.
        x = self.conv2(x)

        # 두 번째 합성곱 이후 텐서 크기를 출력합니다.
        print(f"두 번째 합성곱        : {tuple(x.shape)}")

        # 두 번째 ReLU 활성화 함수를 적용합니다.
        x = self.relu2(x)

        # 두 번째 ReLU 이후 텐서 크기를 출력합니다.
        print(f"두 번째 ReLU          : {tuple(x.shape)}")

        # 두 번째 최대 풀링을 적용합니다.
        x = self.pool2(x)

        # 두 번째 최대 풀링 이후 텐서 크기를 출력합니다.
        print(f"두 번째 최대 풀링     : {tuple(x.shape)}")

        # 배치 차원은 유지하고 나머지 차원을 하나의 벡터로 평탄화합니다.
        x = torch.flatten(
            x,
            start_dim=1,
        )

        # 평탄화 이후 텐서 크기를 출력합니다.
        print(f"평탄화                : {tuple(x.shape)}")

        # 첫 번째 완전연결 계층을 적용합니다.
        x = self.fc1(x)

        # 첫 번째 완전연결 계층 이후 텐서 크기를 출력합니다.
        print(f"첫 번째 완전연결      : {tuple(x.shape)}")

        # 세 번째 ReLU 활성화 함수를 적용합니다.
        x = self.relu3(x)

        # 출력 완전연결 계층을 적용하여 클래스 로짓을 생성합니다.
        x = self.fc2(x)

        # 최종 클래스 로짓의 텐서 크기를 출력합니다.
        print(f"최종 클래스 로짓      : {tuple(x.shape)}")

        # 최종 로짓 텐서를 반환합니다.
        return x


def run_pytorch_forward_demo() -> None:
    """
    임의의 이미지 텐서를 생성하여 CNN의 순전파를 실행합니다.
    """

    # 실습 제목을 출력합니다.
    print("\n[7. PyTorch CNN 순전파와 텐서 크기 확인]")

    # 실습 결과가 반복 실행할 때 동일하도록 난수 시드를 고정합니다.
    torch.manual_seed(42)

    # 계층별 크기를 출력하는 CNN 모델 객체를 생성합니다.
    model = ShapeTracingCNN()

    # 배치 크기 4, 채널 1, 높이 28, 너비 28인 임의 이미지 텐서를 생성합니다.
    sample_images = torch.randn(
        4,
        1,
        28,
        28,
    )

    # 기울기 계산이 필요 없는 추론 모드 문맥을 시작합니다.
    with torch.no_grad():
        # 샘플 이미지를 모델에 전달하여 순전파를 실행합니다.
        logits = model(sample_images)

    # 첫 번째 샘플의 클래스별 로짓을 출력합니다.
    print("\n첫 번째 샘플의 클래스 로짓:")

    # 첫 번째 이미지에 해당하는 로짓 값을 출력합니다.
    print(logits[0])

    # 가장 큰 로짓을 가진 클래스 인덱스를 계산합니다.
    predicted_class = torch.argmax(
        logits[0],
        dim=0,
    ).item()

    # 현재 모델은 학습 전이므로 결과가 의미 있는 분류가 아님을 알립니다.
    print(f"\n가장 큰 로짓의 클래스 인덱스: {predicted_class}")

    # 임의 초기화 모델의 예측이라는 점을 설명합니다.
    print("현재 모델은 학습 전이므로 예측값 자체보다 텐서 크기 변화에 집중합니다.")
