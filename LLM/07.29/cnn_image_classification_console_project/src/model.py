"""RGB 이미지를 분류하는 CNN 모델을 정의합니다."""

# 텐서 연산을 위해 PyTorch를 가져옵니다.
import torch

# 신경망 계층을 정의하기 위해 torch.nn을 가져옵니다.
import torch.nn as nn


class ImageClassifierCNN(nn.Module):
    """세 개의 합성곱 블록과 글로벌 평균 풀링을 사용하는 CNN입니다."""

    def __init__(self, num_classes: int) -> None:
        """클래스 수에 맞게 특징 추출기와 분류기를 구성합니다."""

        # nn.Module 부모 클래스 초기화를 수행합니다.
        super().__init__()

        # 첫 번째 특징 추출 블록을 정의합니다.
        self.features = nn.Sequential(
            # RGB 3채널을 32개 특징 채널로 변환합니다.
            nn.Conv2d(3, 32, kernel_size=3, stride=1, padding=1, bias=False),
            # 32개 채널의 분포를 배치 단위로 정규화합니다.
            nn.BatchNorm2d(32),
            # 비선형성을 추가합니다.
            nn.ReLU(inplace=True),
            # 가로와 세로 크기를 절반으로 줄입니다.
            nn.MaxPool2d(kernel_size=2, stride=2),

            # 32개 특징 채널을 64개로 확장합니다.
            nn.Conv2d(32, 64, kernel_size=3, stride=1, padding=1, bias=False),
            # 64개 채널을 배치 정규화합니다.
            nn.BatchNorm2d(64),
            # 비선형성을 추가합니다.
            nn.ReLU(inplace=True),
            # 공간 크기를 다시 절반으로 줄입니다.
            nn.MaxPool2d(kernel_size=2, stride=2),

            # 64개 특징 채널을 128개로 확장합니다.
            nn.Conv2d(64, 128, kernel_size=3, stride=1, padding=1, bias=False),
            # 128개 채널을 배치 정규화합니다.
            nn.BatchNorm2d(128),
            # 비선형성을 추가합니다.
            nn.ReLU(inplace=True),
            # 공간 크기를 다시 절반으로 줄입니다.
            nn.MaxPool2d(kernel_size=2, stride=2),
        )

        # 입력 이미지 크기와 관계없이 채널당 하나의 값만 남깁니다.
        self.global_pool = nn.AdaptiveAvgPool2d((1, 1))

        # 최종 클래스 로짓을 생성하는 분류기를 정의합니다.
        self.classifier = nn.Sequential(
            # 학습 중 30%의 특징을 무작위로 비활성화합니다.
            nn.Dropout(p=0.3),
            # 128개 특징을 클래스 수만큼의 로짓으로 변환합니다.
            nn.Linear(128, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """입력 이미지를 특징 추출기와 분류기에 전달합니다."""

        # 합성곱 블록을 통과시켜 공간 특징을 추출합니다.
        x = self.features(x)

        # 각 채널의 공간 값을 평균하여 1×1로 압축합니다.
        x = self.global_pool(x)

        # 배치 차원을 유지하면서 나머지 차원을 1차원으로 평탄화합니다.
        x = torch.flatten(x, start_dim=1)

        # 분류기를 통과시켜 클래스별 로짓을 계산합니다.
        x = self.classifier(x)

        # 계산된 로짓을 반환합니다.
        return x
