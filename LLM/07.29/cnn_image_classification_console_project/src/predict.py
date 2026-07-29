"""저장된 최적 모델로 단일 이미지를 분류합니다."""

# 사용자 입력 이미지 경로를 처리하기 위해 Path를 가져옵니다.
from pathlib import Path

# 이미지 파일을 열기 위해 Pillow의 Image를 가져옵니다.
from PIL import Image

# 모델 로딩과 추론을 위해 PyTorch를 가져옵니다.
import torch

# 이미지 전처리 파이프라인을 만들기 위해 transforms를 가져옵니다.
from torchvision import transforms

# 프로젝트 설정 클래스를 가져옵니다.
from src.config import Config

# CNN 모델 클래스를 가져옵니다.
from src.model import ImageClassifierCNN

# CPU 또는 GPU 장치를 선택하는 함수를 가져옵니다.
from src.utils import get_device


def predict_image(config: Config, image_path: str) -> None:
    """하나의 이미지 파일을 분류하고 클래스별 확률을 출력합니다."""

    # 단일 이미지 추론 제목을 출력합니다.
    print("\n[단일 이미지 분류]")

    # 사용자가 입력한 경로 문자열을 Path 객체로 변환합니다.
    path = Path(image_path)

    # 이미지 파일 존재 여부를 검사합니다.
    if not path.exists():
        # 파일이 없으면 정확한 경로를 입력하도록 오류를 발생시킵니다.
        raise FileNotFoundError(f"이미지를 찾을 수 없습니다: {path}")

    # 최적 모델 파일 존재 여부를 검사합니다.
    if not config.best_model_path.exists():
        # 모델이 없으면 먼저 학습을 실행하도록 오류를 발생시킵니다.
        raise FileNotFoundError("best_model.pt가 없습니다. 먼저 모델을 학습하세요.")

    # 저장된 최적 모델 데이터를 CPU 메모리로 불러옵니다.
    saved = torch.load(config.best_model_path, map_location="cpu", weights_only=False)

    # 저장된 클래스 수에 맞는 CNN 모델을 생성합니다.
    model = ImageClassifierCNN(num_classes=saved["num_classes"])

    # 저장된 모델 가중치를 복원합니다.
    model.load_state_dict(saved["model_state_dict"])

    # CPU 또는 CUDA 실행 장치를 선택합니다.
    device = get_device()

    # 모델을 선택된 장치로 이동합니다.
    model = model.to(device)

    # 드롭아웃과 배치 정규화를 추론 모드로 전환합니다.
    model.eval()

    # 저장된 입력 크기에 맞는 이미지 전처리를 정의합니다.
    transform = transforms.Compose([
        # 입력 이미지를 학습에 사용한 크기로 조절합니다.
        transforms.Resize((saved["image_size"], saved["image_size"])),
        # PIL 이미지를 텐서로 변환합니다.
        transforms.ToTensor(),
        # 학습과 동일한 평균 및 표준편차로 정규화합니다.
        transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5]),
    ])

    # 이미지 파일을 열고 RGB 3채널 형태로 변환합니다.
    image = Image.open(path).convert("RGB")

    # 이미지를 전처리한 뒤 배치 차원 하나를 추가합니다.
    image_tensor = transform(image).unsqueeze(0).to(device)

    # 추론에는 기울기 계산이 필요 없으므로 자동 미분을 비활성화합니다.
    with torch.no_grad():
        # 모델 순전파로 클래스별 로짓을 계산합니다.
        logits = model(image_tensor)

        # 로짓을 클래스 확률로 변환합니다.
        probabilities = torch.softmax(logits, dim=1)

        # 가장 높은 확률과 해당 클래스 인덱스를 가져옵니다.
        confidence, predicted_index = torch.max(probabilities, dim=1)

    # 예측 클래스 인덱스를 Python 정수로 변환합니다.
    predicted_index = predicted_index.item()

    # 예측 신뢰도를 Python 실수로 변환합니다.
    confidence = confidence.item()

    # 클래스 목록에서 예측 클래스 이름을 가져옵니다.
    predicted_class = saved["class_names"][predicted_index]

    # 예측 클래스 이름을 출력합니다.
    print(f"예측 클래스: {predicted_class}")

    # 예측 신뢰도를 백분율로 출력합니다.
    print(f"신뢰도: {confidence * 100:.2f}%")

    # 모든 클래스별 확률을 출력하기 위한 제목을 표시합니다.
    print("\n클래스별 확률")

    # 클래스 이름과 확률을 한 쌍씩 반복합니다.
    for class_name, probability in zip(saved["class_names"], probabilities[0].cpu().tolist()):
        # 현재 클래스의 확률을 백분율로 출력합니다.
        print(f"- {class_name}: {probability * 100:.2f}%")
