"""실제 이미지 로딩, 데이터 분리, 데이터 증강, DataLoader 생성을 담당합니다."""

# 데이터 묶음 클래스를 간결하게 정의하기 위해 dataclass를 가져옵니다.
from dataclasses import dataclass

# 파일과 폴더 경로를 다루기 위해 Path를 가져옵니다.
from pathlib import Path

# 인덱스 목록 타입을 표현하기 위해 Sequence를 가져옵니다.
from typing import Sequence

# 증강 이미지를 파일로 저장하기 위해 matplotlib.pyplot을 가져옵니다.
import matplotlib.pyplot as plt

# 텐서와 난수 생성기를 사용하기 위해 PyTorch를 가져옵니다.
import torch

# Dataset과 DataLoader를 사용하기 위해 관련 클래스를 가져옵니다.
from torch.utils.data import Dataset, DataLoader

# ImageFolder, FakeData, 이미지 변환 기능을 사용하기 위해 torchvision을 가져옵니다.
from torchvision import datasets, transforms

# 여러 이미지를 하나의 그리드로 만들기 위해 make_grid를 가져옵니다.
from torchvision.utils import make_grid

# 프로젝트 설정 클래스를 가져옵니다.
from src.config import Config


@dataclass
class DataBundle:
    """학습, 검증, 테스트 데이터셋과 DataLoader를 묶어 보관합니다."""

    # 학습 데이터셋을 저장합니다.
    train_dataset: Dataset

    # 검증 데이터셋을 저장합니다.
    val_dataset: Dataset

    # 테스트 데이터셋을 저장합니다.
    test_dataset: Dataset

    # 학습 DataLoader를 저장합니다.
    train_loader: DataLoader

    # 검증 DataLoader를 저장합니다.
    val_loader: DataLoader

    # 테스트 DataLoader를 저장합니다.
    test_loader: DataLoader

    # 클래스 이름 목록을 저장합니다.
    class_names: list[str]


class TransformSubset(Dataset):
    """원본 데이터셋의 일부 인덱스에 특정 변환을 적용하는 데이터셋입니다."""

    def __init__(self, base_dataset: Dataset, indices: Sequence[int], transform) -> None:
        """원본 데이터셋, 사용할 인덱스, 이미지 변환을 저장합니다."""

        # 원본 이미지와 레이블을 제공하는 데이터셋을 저장합니다.
        self.base_dataset = base_dataset

        # 현재 분할에서 사용할 인덱스를 리스트로 저장합니다.
        self.indices = list(indices)

        # 현재 분할에 적용할 이미지 변환 파이프라인을 저장합니다.
        self.transform = transform

    def __len__(self) -> int:
        """현재 분할에 포함된 샘플 수를 반환합니다."""

        # 저장된 인덱스 개수를 반환합니다.
        return len(self.indices)

    def __getitem__(self, item: int):
        """현재 분할의 특정 이미지와 레이블을 반환합니다."""

        # 현재 위치를 원본 데이터셋 인덱스로 변환합니다.
        original_index = self.indices[item]

        # 원본 데이터셋에서 이미지와 레이블을 읽습니다.
        image, label = self.base_dataset[original_index]

        # 이미지 변환이 설정되어 있으면 해당 변환을 적용합니다.
        if self.transform is not None:
            # 학습 또는 평가용 변환을 이미지에 적용합니다.
            image = self.transform(image)

        # 변환된 이미지와 레이블을 반환합니다.
        return image, label


def build_transforms(config: Config):
    """학습용 증강 변환과 검증·테스트용 변환을 생성합니다."""

    # 학습 데이터에만 적용할 무작위 증강 파이프라인을 정의합니다.
    train_transform = transforms.Compose([
        # 이미지 일부를 무작위로 잘라 지정한 크기로 조절합니다.
        transforms.RandomResizedCrop(config.image_size, scale=(0.75, 1.0)),
        # 50% 확률로 이미지를 좌우 반전합니다.
        transforms.RandomHorizontalFlip(p=0.5),
        # 이미지를 -15도에서 15도 사이로 무작위 회전합니다.
        transforms.RandomRotation(degrees=15),
        # 밝기, 대비, 채도를 무작위로 변경합니다.
        transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
        # PIL 이미지를 [채널, 높이, 너비] 텐서로 변환합니다.
        transforms.ToTensor(),
        # 각 RGB 채널을 평균 0.5와 표준편차 0.5로 정규화합니다.
        transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5]),
    ])

    # 검증과 테스트에 적용할 결정론적 변환 파이프라인을 정의합니다.
    eval_transform = transforms.Compose([
        # 모든 이미지를 모델 입력 크기로 조절합니다.
        transforms.Resize((config.image_size, config.image_size)),
        # PIL 이미지를 텐서로 변환합니다.
        transforms.ToTensor(),
        # 학습 데이터와 동일한 방식으로 정규화합니다.
        transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5]),
    ])

    # 두 변환 파이프라인을 반환합니다.
    return train_transform, eval_transform


def has_real_images(data_dir: Path) -> bool:
    """data/images가 ImageFolder 형식의 실제 데이터인지 확인합니다."""

    # 지원할 이미지 확장자 집합을 정의합니다.
    valid_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

    # data/images 바로 아래의 하위 폴더를 클래스 폴더로 수집합니다.
    class_dirs = [path for path in data_dir.iterdir() if path.is_dir()]

    # 분류를 위해 클래스 폴더가 최소 두 개 이상인지 검사합니다.
    if len(class_dirs) < 2:
        # 클래스가 부족하면 실제 데이터가 없다고 판단합니다.
        return False

    # 각 클래스 폴더에 이미지 파일이 존재하는지 확인합니다.
    for class_dir in class_dirs:
        # 현재 클래스 폴더 아래의 지원 이미지 파일 목록을 만듭니다.
        image_files = [
            path for path in class_dir.rglob("*")
            if path.is_file() and path.suffix.lower() in valid_extensions
        ]

        # 현재 클래스에 이미지가 없으면 유효하지 않은 데이터 구조입니다.
        if not image_files:
            # 실제 데이터가 없다고 반환합니다.
            return False

    # 모든 클래스 폴더가 조건을 만족하면 실제 데이터가 있다고 반환합니다.
    return True


def create_base_dataset(config: Config):
    """실제 ImageFolder를 우선 사용하고 없으면 FakeData를 사용합니다."""

    # 실제 이미지 데이터 구조가 존재하는지 검사합니다.
    if has_real_images(config.data_dir):
        # 이미지 변환을 적용하지 않은 ImageFolder 원본 데이터셋을 생성합니다.
        dataset = datasets.ImageFolder(root=str(config.data_dir), transform=None)

        # 폴더 이름에서 자동 생성된 클래스 이름 목록을 가져옵니다.
        class_names = dataset.classes

        # 실제 데이터 사용 표시를 반환합니다.
        return dataset, class_names, "ImageFolder"

    # 실제 데이터가 없고 FakeData 사용도 금지된 경우 오류를 발생시킵니다.
    if not config.use_fake_data_if_empty:
        # 올바른 폴더 구조를 만들도록 안내하는 오류를 발생시킵니다.
        raise FileNotFoundError("data/images 아래에 클래스별 이미지 폴더를 생성하세요.")

    # 코드 실행 확인을 위한 FakeData 데이터셋을 생성합니다.
    dataset = datasets.FakeData(
        size=config.fake_data_size,
        image_size=(3, config.image_size, config.image_size),
        num_classes=config.fake_num_classes,
        transform=transforms.ToPILImage(),
        random_offset=config.seed,
    )

    # FakeData의 클래스 이름을 순서대로 생성합니다.
    class_names = [f"class_{index}" for index in range(config.fake_num_classes)]

    # FakeData 데이터셋과 클래스 이름을 반환합니다.
    return dataset, class_names, "FakeData"


def split_indices(total_size: int, config: Config):
    """전체 샘플 인덱스를 학습, 검증, 테스트로 무작위 분리합니다."""

    # 세 분할을 만들 수 있도록 최소 데이터 수를 검사합니다.
    if total_size < 3:
        # 데이터가 너무 적으면 명확한 오류를 발생시킵니다.
        raise ValueError("학습/검증/테스트 분리를 위해 최소 3개의 이미지가 필요합니다.")

    # 고정된 시드로 독립적인 PyTorch 난수 생성기를 만듭니다.
    generator = torch.Generator().manual_seed(config.seed)

    # 전체 샘플 인덱스를 무작위 순서로 섞습니다.
    indices = torch.randperm(total_size, generator=generator).tolist()

    # 학습 데이터 수를 계산합니다.
    train_size = int(total_size * config.train_ratio)

    # 검증 데이터 수를 계산합니다.
    val_size = int(total_size * config.val_ratio)

    # 남은 데이터를 테스트 데이터 수로 사용합니다.
    test_size = total_size - train_size - val_size

    # 각 분할에 최소 한 개 이상의 샘플이 있는지 검사합니다.
    if min(train_size, val_size, test_size) < 1:
        # 데이터 수가 부족함을 알리는 오류를 발생시킵니다.
        raise ValueError("각 분할에 최소 1개 이상 배정되도록 이미지를 추가하세요.")

    # 섞인 인덱스 앞부분을 학습 인덱스로 사용합니다.
    train_indices = indices[:train_size]

    # 학습 구간 다음 부분을 검증 인덱스로 사용합니다.
    val_indices = indices[train_size:train_size + val_size]

    # 나머지 인덱스를 테스트 인덱스로 사용합니다.
    test_indices = indices[train_size + val_size:]

    # 세 종류의 인덱스를 반환합니다.
    return train_indices, val_indices, test_indices


def prepare_dataloaders(config: Config) -> DataBundle:
    """분할 데이터셋과 학습·검증·테스트 DataLoader를 생성합니다."""

    # 학습 증강과 평가 변환을 생성합니다.
    train_transform, eval_transform = build_transforms(config)

    # 실제 또는 가짜 원본 데이터셋을 생성합니다.
    base_dataset, class_names, source = create_base_dataset(config)

    # 전체 인덱스를 학습, 검증, 테스트로 나눕니다.
    train_indices, val_indices, test_indices = split_indices(len(base_dataset), config)

    # 학습 인덱스에만 무작위 데이터 증강을 적용합니다.
    train_dataset = TransformSubset(base_dataset, train_indices, train_transform)

    # 검증 인덱스에는 무작위성이 없는 평가 변환을 적용합니다.
    val_dataset = TransformSubset(base_dataset, val_indices, eval_transform)

    # 테스트 인덱스에도 동일한 평가 변환을 적용합니다.
    test_dataset = TransformSubset(base_dataset, test_indices, eval_transform)

    # CUDA 사용 시 페이지 고정 메모리를 사용할지 결정합니다.
    pin_memory = torch.cuda.is_available()

    # 학습 데이터를 섞어서 미니배치로 제공하는 DataLoader를 생성합니다.
    train_loader = DataLoader(
        train_dataset,
        batch_size=config.batch_size,
        shuffle=True,
        num_workers=config.num_workers,
        pin_memory=pin_memory,
    )

    # 검증 데이터를 고정 순서로 제공하는 DataLoader를 생성합니다.
    val_loader = DataLoader(
        val_dataset,
        batch_size=config.batch_size,
        shuffle=False,
        num_workers=config.num_workers,
        pin_memory=pin_memory,
    )

    # 테스트 데이터를 고정 순서로 제공하는 DataLoader를 생성합니다.
    test_loader = DataLoader(
        test_dataset,
        batch_size=config.batch_size,
        shuffle=False,
        num_workers=config.num_workers,
        pin_memory=pin_memory,
    )

    # 사용한 데이터 출처를 출력합니다.
    print(f"\n데이터 출처: {source}")

    # 데이터 묶음 객체를 생성하여 반환합니다.
    return DataBundle(
        train_dataset=train_dataset,
        val_dataset=val_dataset,
        test_dataset=test_dataset,
        train_loader=train_loader,
        val_loader=val_loader,
        test_loader=test_loader,
        class_names=class_names,
    )


def inspect_dataset(config: Config) -> None:
    """데이터셋 출처, 전체 수량, 클래스 정보를 출력합니다."""

    # 데이터셋 점검 제목을 출력합니다.
    print("\n[데이터셋 구조와 클래스 정보]")

    # 실제 또는 가짜 원본 데이터셋을 생성합니다.
    dataset, class_names, source = create_base_dataset(config)

    # 데이터 출처를 출력합니다.
    print(f"데이터 출처: {source}")

    # 전체 이미지 수를 출력합니다.
    print(f"전체 이미지 수: {len(dataset)}")

    # 클래스 이름 목록을 출력합니다.
    print(f"클래스 목록: {class_names}")

    # 실제 ImageFolder인 경우 클래스별 이미지 수를 출력합니다.
    if source == "ImageFolder":
        # 각 클래스 이름과 인덱스를 순서대로 반복합니다.
        for class_index, class_name in enumerate(class_names):
            # 현재 클래스 인덱스와 같은 레이블 수를 계산합니다.
            count = sum(1 for target in dataset.targets if target == class_index)
            # 클래스 이름과 이미지 수를 출력합니다.
            print(f"- {class_name}: {count}장")
    else:
        # FakeData 사용 시 실제 이미지 폴더 구조를 안내합니다.
        print("\n실제 이미지를 사용하려면 다음 구조로 배치하세요.")
        # ImageFolder 구조 예시를 출력합니다.
        print("data/images/cat/*.jpg\ndata/images/dog/*.jpg")


def denormalize(tensor: torch.Tensor) -> torch.Tensor:
    """평균 0.5, 표준편차 0.5 정규화를 시각화 범위로 되돌립니다."""

    # 정규화 역변환을 적용합니다.
    tensor = tensor * 0.5 + 0.5

    # 픽셀값을 0과 1 사이로 제한해 반환합니다.
    return tensor.clamp(0.0, 1.0)


def save_augmentation_preview(config: Config) -> None:
    """동일 이미지의 원본과 증강 결과를 하나의 PNG로 저장합니다."""

    # 증강 미리보기 제목을 출력합니다.
    print("\n[데이터 증강 미리보기 저장]")

    # 학습용 증강과 평가용 변환을 생성합니다.
    train_transform, eval_transform = build_transforms(config)

    # 원본 데이터셋을 생성합니다.
    dataset, class_names, source = create_base_dataset(config)

    # 첫 번째 이미지와 레이블을 가져옵니다.
    original_image, label = dataset[0]

    # 원본 이미지에는 평가 변환을 적용합니다.
    images = [eval_transform(original_image)]

    # 동일한 원본에 학습 증강을 일곱 번 적용합니다.
    for _ in range(7):
        # 무작위 증강 결과를 목록에 추가합니다.
        images.append(train_transform(original_image))

    # 이미지 목록을 하나의 배치 텐서로 결합합니다.
    batch = torch.stack(images)

    # 사람이 볼 수 있도록 정규화를 되돌립니다.
    batch = denormalize(batch)

    # 네 개 열로 이미지를 배치한 그리드를 생성합니다.
    grid = make_grid(batch, nrow=4, padding=4)

    # 증강 미리보기 그림 객체를 생성합니다.
    plt.figure(figsize=(12, 7))

    # 텐서 채널 순서를 이미지 표시 형식으로 바꾸어 출력합니다.
    plt.imshow(grid.permute(1, 2, 0).cpu().numpy())

    # 축 눈금을 숨깁니다.
    plt.axis("off")

    # 데이터 출처와 클래스 이름을 제목으로 표시합니다.
    plt.title(f"Original + Augmentation | {source} | {class_names[label]}")

    # 그림 여백을 자동 조절합니다.
    plt.tight_layout()

    # 저장할 파일 경로를 설정합니다.
    output_path = config.preview_dir / "augmentation_preview.png"

    # 그림을 PNG 파일로 저장합니다.
    plt.savefig(output_path, dpi=150, bbox_inches="tight")

    # 그림 객체를 닫아 메모리를 해제합니다.
    plt.close()

    # 저장 경로를 출력합니다.
    print(f"저장 완료: {output_path}")
