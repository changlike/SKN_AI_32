"""
외부 데이터 다운로드 없이 합성 이미지로 CNN 학습과 역전파를 확인하는 모듈입니다.
"""

# 텐서 연산과 자동 미분을 사용하기 위해 PyTorch를 가져옵니다.
import torch

# 신경망 계층과 손실 함수를 사용하기 위해 torch.nn을 가져옵니다.
import torch.nn as nn

# 데이터셋과 데이터 로더를 사용하기 위해 관련 클래스를 가져옵니다.
from torch.utils.data import DataLoader, TensorDataset


class TinyPatternCNN(nn.Module):
    """
    세로선 이미지와 가로선 이미지를 구분하는 작은 CNN 모델입니다.
    """

    def __init__(self) -> None:
        """
        특징 추출 계층과 분류 계층을 정의합니다.
        """

        # nn.Module 부모 클래스의 초기화 기능을 호출합니다.
        super().__init__()

        # 1채널 입력에서 4개의 특징 맵을 만드는 합성곱 계층을 정의합니다.
        self.conv = nn.Conv2d(
            in_channels=1,
            out_channels=4,
            kernel_size=3,
            stride=1,
            padding=1,
        )

        # 합성곱 출력에 비선형성을 추가할 ReLU를 정의합니다.
        self.relu = nn.ReLU()

        # 8×8 공간 크기를 4×4로 줄일 최대 풀링 계층을 정의합니다.
        self.pool = nn.MaxPool2d(
            kernel_size=2,
            stride=2,
        )

        # 4×4×4 특징을 2개 클래스 로짓으로 변환하는 완전연결 계층을 정의합니다.
        self.fc = nn.Linear(
            in_features=4 * 4 * 4,
            out_features=2,
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        합성곱, ReLU, 풀링, 평탄화, 완전연결 순서로 순전파합니다.
        """

        # 입력 이미지에 합성곱을 적용하여 지역 특징을 추출합니다.
        x = self.conv(x)

        # 합성곱 출력에 ReLU를 적용합니다.
        x = self.relu(x)

        # 최대 풀링으로 공간 크기를 절반으로 줄입니다.
        x = self.pool(x)

        # 배치 차원은 유지하고 나머지 차원을 하나의 벡터로 평탄화합니다.
        x = torch.flatten(
            x,
            start_dim=1,
        )

        # 평탄화한 특징을 완전연결 계층에 전달하여 클래스 로짓을 계산합니다.
        x = self.fc(x)

        # 최종 클래스 로짓을 반환합니다.
        return x


def create_synthetic_dataset(
    samples_per_class: int = 100,
) -> tuple[torch.Tensor, torch.Tensor]:
    """
    세로선과 가로선으로 구성된 간단한 8×8 이미지 데이터셋을 생성합니다.
    """

    # 실습을 반복해도 같은 데이터가 생성되도록 난수 시드를 고정합니다.
    torch.manual_seed(42)

    # 생성된 이미지들을 저장할 리스트를 만듭니다.
    images = []

    # 각 이미지의 정답 레이블을 저장할 리스트를 만듭니다.
    labels = []

    # 클래스별 샘플 수만큼 반복합니다.
    for _ in range(samples_per_class):
        # 8×8 크기의 세로선 클래스 이미지를 0으로 초기화합니다.
        vertical_image = torch.zeros(
            1,
            8,
            8,
        )

        # 이미지 중앙의 두 열을 1로 설정하여 세로선을 만듭니다.
        vertical_image[:, :, 3:5] = 1.0

        # 데이터가 지나치게 단순하지 않도록 작은 가우시안 잡음을 추가합니다.
        vertical_image = vertical_image + (
            torch.randn_like(vertical_image) * 0.05
        )

        # 생성한 세로선 이미지를 이미지 목록에 추가합니다.
        images.append(vertical_image)

        # 세로선 클래스의 정답 레이블 0을 추가합니다.
        labels.append(0)

        # 8×8 크기의 가로선 클래스 이미지를 0으로 초기화합니다.
        horizontal_image = torch.zeros(
            1,
            8,
            8,
        )

        # 이미지 중앙의 두 행을 1로 설정하여 가로선을 만듭니다.
        horizontal_image[:, 3:5, :] = 1.0

        # 데이터가 지나치게 단순하지 않도록 작은 가우시안 잡음을 추가합니다.
        horizontal_image = horizontal_image + (
            torch.randn_like(horizontal_image) * 0.05
        )

        # 생성한 가로선 이미지를 이미지 목록에 추가합니다.
        images.append(horizontal_image)

        # 가로선 클래스의 정답 레이블 1을 추가합니다.
        labels.append(1)

    # 이미지 리스트를 하나의 4차원 텐서로 결합합니다.
    image_tensor = torch.stack(images)

    # 레이블 리스트를 정수형 텐서로 변환합니다.
    label_tensor = torch.tensor(
        labels,
        dtype=torch.long,
    )

    # 생성한 이미지 텐서와 레이블 텐서를 반환합니다.
    return image_tensor, label_tensor


def calculate_accuracy(
    logits: torch.Tensor,
    labels: torch.Tensor,
) -> float:
    """
    클래스 로짓과 정답 레이블을 사용하여 정확도를 계산합니다.
    """

    # 각 샘플에서 가장 큰 로짓을 가진 클래스 인덱스를 선택합니다.
    predictions = torch.argmax(
        logits,
        dim=1,
    )

    # 예측값과 정답이 같은지 비교한 결과를 실수형으로 변환합니다.
    correct = (predictions == labels).float()

    # 정답 여부의 평균을 계산하여 정확도를 구합니다.
    accuracy = correct.mean().item()

    # 계산한 정확도를 반환합니다.
    return accuracy


def run_training_demo() -> None:
    """
    간단한 CNN을 학습하여 손실 감소와 정확도 증가를 확인합니다.
    """

    # 실습 제목을 출력합니다.
    print("\n[9. 간단한 CNN 학습과 역전파 확인]")

    # 실험 결과의 재현성을 높이기 위해 PyTorch 난수 시드를 고정합니다.
    torch.manual_seed(42)

    # 세로선과 가로선으로 구성된 합성 데이터셋을 생성합니다.
    images, labels = create_synthetic_dataset(
        samples_per_class=100,
    )

    # 이미지와 레이블을 PyTorch 데이터셋 객체로 묶습니다.
    dataset = TensorDataset(
        images,
        labels,
    )

    # 미니배치 단위로 데이터를 제공하는 데이터 로더를 생성합니다.
    dataloader = DataLoader(
        dataset,
        batch_size=20,
        shuffle=True,
    )

    # 두 종류의 패턴을 분류할 작은 CNN 모델을 생성합니다.
    model = TinyPatternCNN()

    # 다중 클래스 분류에 사용할 교차 엔트로피 손실 함수를 생성합니다.
    criterion = nn.CrossEntropyLoss()

    # 확률적 경사하강법 옵티마이저를 생성합니다.
    optimizer = torch.optim.SGD(
        model.parameters(),
        lr=0.1,
    )

    # 학습 전 첫 번째 합성곱 필터의 일부 값을 복사해 둡니다.
    initial_weight = model.conv.weight.detach().clone()

    # 총 학습 반복 횟수를 10 에포크로 설정합니다.
    epochs = 10

    # 설정한 에포크 수만큼 전체 데이터 학습을 반복합니다.
    for epoch in range(1, epochs + 1):
        # 현재 에포크의 누적 손실을 0으로 초기화합니다.
        total_loss = 0.0

        # 현재 에포크의 누적 정확도 계산용 정답 개수를 0으로 초기화합니다.
        total_correct = 0

        # 현재 에포크에서 처리한 전체 샘플 수를 0으로 초기화합니다.
        total_samples = 0

        # 데이터 로더에서 미니배치 이미지와 레이블을 순서대로 가져옵니다.
        for batch_images, batch_labels in dataloader:
            # 이전 반복에서 계산된 기울기를 0으로 초기화합니다.
            optimizer.zero_grad()

            # 미니배치 이미지를 모델에 전달하여 클래스 로짓을 계산합니다.
            logits = model(batch_images)

            # 모델의 로짓과 실제 정답을 비교하여 손실을 계산합니다.
            loss = criterion(
                logits,
                batch_labels,
            )

            # 손실을 기준으로 모든 학습 파라미터의 기울기를 계산합니다.
            loss.backward()

            # 계산된 기울기를 이용하여 커널과 가중치를 갱신합니다.
            optimizer.step()

            # 현재 미니배치 손실에 샘플 수를 곱하여 누적 손실에 더합니다.
            total_loss += loss.item() * batch_images.size(0)

            # 현재 미니배치에서 가장 큰 로짓을 가진 클래스를 선택합니다.
            predictions = torch.argmax(
                logits,
                dim=1,
            )

            # 현재 미니배치의 정답 개수를 누적합니다.
            total_correct += (
                predictions == batch_labels
            ).sum().item()

            # 현재 미니배치의 샘플 수를 전체 처리 샘플 수에 더합니다.
            total_samples += batch_images.size(0)

        # 전체 샘플 수로 나누어 현재 에포크의 평균 손실을 계산합니다.
        average_loss = total_loss / total_samples

        # 전체 샘플 중 정답 비율을 계산하여 현재 에포크 정확도를 구합니다.
        accuracy = total_correct / total_samples

        # 현재 에포크 번호, 평균 손실, 정확도를 출력합니다.
        print(
            f"Epoch {epoch:02d} | "
            f"평균 손실: {average_loss:.6f} | "
            f"정확도: {accuracy * 100:6.2f}%"
        )

    # 평가 시 드롭아웃이나 배치 정규화가 올바르게 동작하도록 평가 모드로 전환합니다.
    model.eval()

    # 평가 과정에서는 기울기 계산이 필요 없으므로 자동 미분을 비활성화합니다.
    with torch.no_grad():
        # 전체 이미지를 모델에 전달하여 최종 로짓을 계산합니다.
        final_logits = model(images)

        # 최종 로짓과 레이블을 이용하여 전체 데이터 정확도를 계산합니다.
        final_accuracy = calculate_accuracy(
            logits=final_logits,
            labels=labels,
        )

    # 학습 후 첫 번째 합성곱 필터의 가중치를 가져옵니다.
    trained_weight = model.conv.weight.detach().clone()

    # 학습 전후 커널 가중치의 절대 변화량 평균을 계산합니다.
    mean_weight_change = torch.mean(
        torch.abs(trained_weight - initial_weight)
    ).item()

    # 최종 학습 정확도를 출력합니다.
    print(f"\n최종 학습 정확도: {final_accuracy * 100:.2f}%")

    # 역전파와 옵티마이저 갱신으로 필터 값이 실제 변경되었음을 출력합니다.
    print(
        "첫 번째 합성곱 계층 가중치의 평균 절대 변화량: "
        f"{mean_weight_change:.8f}"
    )

    # 필터가 학습을 통해 변경된 의미를 설명합니다.
    print("\n손실의 역전파 결과에 따라 합성곱 커널이 갱신되었습니다.")

    # 모델이 세로선과 가로선 특징을 구분하도록 학습되었음을 설명합니다.
    print("CNN은 세로선과 가로선의 공간 패턴을 자동으로 학습합니다.")
