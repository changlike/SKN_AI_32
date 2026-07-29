"""프로젝트 경로와 학습 하이퍼파라미터를 관리하는 설정 모듈입니다."""

# 간결한 설정 클래스를 작성하기 위해 dataclass와 field를 가져옵니다.
from dataclasses import dataclass, field

# 운영체제와 독립적으로 경로를 처리하기 위해 Path를 가져옵니다.
from pathlib import Path


@dataclass
class Config:
    """프로젝트에서 사용하는 모든 설정값을 보관합니다."""

    # 현재 프로젝트의 루트 폴더를 자동 계산합니다.
    project_root: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent)

    # 원본 이미지 폴더 경로는 초기화 후 계산합니다.
    data_dir: Path = field(init=False)

    # 모델 및 체크포인트 저장 폴더 경로는 초기화 후 계산합니다.
    artifacts_dir: Path = field(init=False)

    # 학습 로그 저장 폴더 경로는 초기화 후 계산합니다.
    logs_dir: Path = field(init=False)

    # 증강 미리보기 저장 폴더 경로는 초기화 후 계산합니다.
    preview_dir: Path = field(init=False)

    # 최적 모델 파일 경로는 초기화 후 계산합니다.
    best_model_path: Path = field(init=False)

    # 마지막 체크포인트 파일 경로는 초기화 후 계산합니다.
    checkpoint_path: Path = field(init=False)

    # 학습 이력 CSV 파일 경로는 초기화 후 계산합니다.
    history_path: Path = field(init=False)

    # 학습 곡선 이미지 경로는 초기화 후 계산합니다.
    curve_path: Path = field(init=False)

    # 모델에 입력할 정사각형 이미지 한 변의 크기를 설정합니다.
    image_size: int = 128

    # 한 번에 처리할 이미지 수를 설정합니다.
    batch_size: int = 16

    # 신규 학습의 최대 에포크 수를 설정합니다.
    epochs: int = 30

    # 체크포인트 재개 시 추가 학습할 에포크 수를 설정합니다.
    resume_epochs: int = 10

    # AdamW 옵티마이저의 초기 학습률을 설정합니다.
    learning_rate: float = 0.001

    # 과적합 완화를 위한 가중치 감쇠 값을 설정합니다.
    weight_decay: float = 0.0001

    # 검증 손실이 개선되지 않아도 기다릴 최대 에포크 수를 설정합니다.
    early_stopping_patience: int = 5

    # 개선으로 인정할 검증 손실의 최소 감소량을 설정합니다.
    early_stopping_min_delta: float = 0.0001

    # 전체 데이터 중 학습 데이터 비율을 설정합니다.
    train_ratio: float = 0.70

    # 전체 데이터 중 검증 데이터 비율을 설정합니다.
    val_ratio: float = 0.15

    # 전체 데이터 중 테스트 데이터 비율을 설정합니다.
    test_ratio: float = 0.15

    # 데이터 분할과 학습의 재현성을 위한 난수 시드를 설정합니다.
    seed: int = 42

    # Windows PyCharm에서 안정적으로 실행하도록 DataLoader 작업자 수를 0으로 설정합니다.
    num_workers: int = 0

    # 실제 이미지가 없을 때 프로그램 검증용 FakeData를 사용할지 설정합니다.
    use_fake_data_if_empty: bool = True

    # FakeData로 생성할 전체 이미지 수를 설정합니다.
    fake_data_size: int = 300

    # FakeData에서 사용할 클래스 수를 설정합니다.
    fake_num_classes: int = 3

    def __post_init__(self) -> None:
        """기본 필드 생성 후 경로를 계산하고 폴더를 생성합니다."""

        # 실제 이미지가 저장될 data/images 폴더를 설정합니다.
        self.data_dir = self.project_root / "data" / "images"

        # 모델과 체크포인트가 저장될 artifacts 폴더를 설정합니다.
        self.artifacts_dir = self.project_root / "artifacts"

        # 학습 로그가 저장될 logs 폴더를 설정합니다.
        self.logs_dir = self.project_root / "logs"

        # 데이터 증강 미리보기가 저장될 폴더를 설정합니다.
        self.preview_dir = self.artifacts_dir / "previews"

        # 검증 손실이 가장 낮은 모델의 파일 경로를 설정합니다.
        self.best_model_path = self.artifacts_dir / "best_model.pt"

        # 매 에포크 마지막 학습 상태를 저장할 파일 경로를 설정합니다.
        self.checkpoint_path = self.artifacts_dir / "last_checkpoint.pt"

        # 에포크별 학습 이력을 저장할 CSV 경로를 설정합니다.
        self.history_path = self.logs_dir / "training_history.csv"

        # 손실과 정확도 곡선을 저장할 이미지 경로를 설정합니다.
        self.curve_path = self.logs_dir / "training_curves.png"

        # 데이터 폴더를 생성합니다.
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # 모델 저장 폴더를 생성합니다.
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)

        # 로그 저장 폴더를 생성합니다.
        self.logs_dir.mkdir(parents=True, exist_ok=True)

        # 증강 미리보기 저장 폴더를 생성합니다.
        self.preview_dir.mkdir(parents=True, exist_ok=True)

        # 데이터 분할 비율의 합계를 계산합니다.
        ratio_sum = self.train_ratio + self.val_ratio + self.test_ratio

        # 비율 합이 1이 아니면 잘못된 설정이므로 예외를 발생시킵니다.
        if abs(ratio_sum - 1.0) > 1e-8:
            # 설정 오류를 알리는 메시지를 포함해 예외를 발생시킵니다.
            raise ValueError("train_ratio + val_ratio + test_ratio는 1이어야 합니다.")
