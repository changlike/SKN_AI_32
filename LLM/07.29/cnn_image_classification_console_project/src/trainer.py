"""모델 학습, 검증, 테스트, 모델 저장, 체크포인트, 조기 종료를 구현합니다."""

# 학습 곡선을 이미지로 저장하기 위해 matplotlib.pyplot을 가져옵니다.
import matplotlib.pyplot as plt

# 모델 저장과 텐서 연산을 위해 PyTorch를 가져옵니다.
import torch

# 손실 함수 타입을 사용하기 위해 torch.nn을 가져옵니다.
import torch.nn as nn

# AdamW 옵티마이저와 학습률 스케줄러를 사용하기 위해 torch.optim을 가져옵니다.
import torch.optim as optim

# 프로젝트 설정을 가져옵니다.
from src.config import Config

# 데이터셋과 DataLoader 준비 기능을 가져옵니다.
from src.data import DataBundle, prepare_dataloaders

# CNN 모델 클래스를 가져옵니다.
from src.model import ImageClassifierCNN

# 장치 선택, 시드 설정, 학습 이력 저장 기능을 가져옵니다.
from src.utils import get_device, set_seed, save_history


class EarlyStopping:
    """검증 손실이 일정 기간 개선되지 않으면 학습을 중단합니다."""

    def __init__(self, patience: int, min_delta: float) -> None:
        """대기 에포크 수와 최소 개선량을 저장합니다."""

        # 개선이 없어도 기다릴 최대 횟수를 저장합니다.
        self.patience = patience

        # 개선으로 인정할 최소 손실 감소량을 저장합니다.
        self.min_delta = min_delta

        # 현재까지의 최적 손실은 아직 없으므로 None으로 설정합니다.
        self.best_loss = None

        # 연속 미개선 횟수를 0으로 초기화합니다.
        self.counter = 0

    def step(self, val_loss: float) -> bool:
        """현재 검증 손실을 확인하고 중단 여부를 반환합니다."""

        # 첫 호출이면 현재 손실을 최적값으로 저장합니다.
        if self.best_loss is None:
            # 첫 검증 손실을 최적값으로 기록합니다.
            self.best_loss = val_loss
            # 아직 중단하지 않으므로 False를 반환합니다.
            return False

        # 현재 손실이 최소 개선량 이상 낮아졌는지 검사합니다.
        if val_loss < self.best_loss - self.min_delta:
            # 최적 손실을 현재 값으로 갱신합니다.
            self.best_loss = val_loss
            # 개선되었으므로 미개선 횟수를 0으로 초기화합니다.
            self.counter = 0
            # 학습을 계속하도록 False를 반환합니다.
            return False

        # 충분한 개선이 없으므로 미개선 횟수를 1 증가시킵니다.
        self.counter += 1

        # 미개선 횟수가 patience 이상이면 True를 반환합니다.
        return self.counter >= self.patience

    def state_dict(self) -> dict:
        """체크포인트에 저장할 상태를 사전으로 반환합니다."""

        # 내부 상태값을 사전으로 구성하여 반환합니다.
        return {"best_loss": self.best_loss, "counter": self.counter}

    def load_state_dict(self, state: dict) -> None:
        """체크포인트에서 조기 종료 상태를 복원합니다."""

        # 저장된 최적 검증 손실을 복원합니다.
        self.best_loss = state.get("best_loss")

        # 저장된 연속 미개선 횟수를 복원합니다.
        self.counter = state.get("counter", 0)


def run_epoch(model, loader, criterion, device, optimizer=None):
    """하나의 학습 또는 평가 에포크를 실행합니다."""

    # 옵티마이저 전달 여부로 학습 모드인지 판단합니다.
    is_training = optimizer is not None

    # 학습 모드이면 모델을 train 상태로 전환합니다.
    if is_training:
        # 드롭아웃과 배치 정규화가 학습 방식으로 동작합니다.
        model.train()
    else:
        # 평가 모드이면 모델을 eval 상태로 전환합니다.
        model.eval()

    # 전체 손실 합계를 0으로 초기화합니다.
    total_loss = 0.0

    # 전체 정답 개수를 0으로 초기화합니다.
    total_correct = 0

    # 전체 처리 샘플 수를 0으로 초기화합니다.
    total_samples = 0

    # 학습 모드에서만 자동 미분을 활성화합니다.
    with torch.set_grad_enabled(is_training):
        # DataLoader의 모든 미니배치를 반복합니다.
        for images, labels in loader:
            # 이미지 텐서를 CPU 또는 GPU 장치로 이동합니다.
            images = images.to(device, non_blocking=True)

            # 레이블 텐서를 같은 장치로 이동합니다.
            labels = labels.to(device, non_blocking=True)

            # 학습 모드이면 이전 기울기를 초기화합니다.
            if is_training:
                # 메모리를 효율적으로 사용하도록 기울기를 None으로 설정합니다.
                optimizer.zero_grad(set_to_none=True)

            # 모델 순전파로 클래스별 로짓을 계산합니다.
            logits = model(images)

            # 로짓과 정답 레이블을 비교하여 손실을 계산합니다.
            loss = criterion(logits, labels)

            # 학습 모드이면 역전파와 파라미터 갱신을 수행합니다.
            if is_training:
                # 손실을 기준으로 모든 파라미터의 기울기를 계산합니다.
                loss.backward()

                # 폭발하는 기울기를 완화하기 위해 기울기 노름을 제한합니다.
                torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=5.0)

                # 계산된 기울기를 이용하여 모델 파라미터를 갱신합니다.
                optimizer.step()

            # 미니배치 평균 손실에 샘플 수를 곱해 누적합니다.
            total_loss += loss.item() * images.size(0)

            # 가장 큰 로짓을 가진 클래스 인덱스를 예측값으로 선택합니다.
            predictions = torch.argmax(logits, dim=1)

            # 예측과 정답이 일치한 샘플 수를 누적합니다.
            total_correct += (predictions == labels).sum().item()

            # 현재 미니배치 샘플 수를 전체 샘플 수에 더합니다.
            total_samples += images.size(0)

    # 전체 샘플 기준 평균 손실을 계산합니다.
    average_loss = total_loss / total_samples

    # 전체 샘플 기준 정확도를 계산합니다.
    accuracy = total_correct / total_samples

    # 평균 손실과 정확도를 반환합니다.
    return average_loss, accuracy


def save_best_model(config, model, class_names, best_val_loss):
    """검증 손실이 가장 낮은 모델을 저장합니다."""

    # 추론에 필요한 모델 상태와 메타데이터를 사전으로 구성합니다.
    payload = {
        "model_state_dict": model.state_dict(),
        "class_names": class_names,
        "num_classes": len(class_names),
        "image_size": config.image_size,
        "best_val_loss": best_val_loss,
    }

    # 최적 모델 데이터를 파일에 저장합니다.
    torch.save(payload, config.best_model_path)


def save_checkpoint(config, model, optimizer, scheduler, early_stopping, epoch, best_val_loss, history, class_names):
    """학습 재개에 필요한 전체 상태를 저장합니다."""

    # 모델과 학습 상태를 하나의 사전으로 구성합니다.
    payload = {
        "epoch": epoch,
        "model_state_dict": model.state_dict(),
        "optimizer_state_dict": optimizer.state_dict(),
        "scheduler_state_dict": scheduler.state_dict(),
        "early_stopping_state": early_stopping.state_dict(),
        "best_val_loss": best_val_loss,
        "history": history,
        "class_names": class_names,
    }

    # 마지막 체크포인트 파일에 전체 상태를 저장합니다.
    torch.save(payload, config.checkpoint_path)


def plot_history(history, output_path):
    """학습 및 검증 손실과 정확도를 하나의 그림으로 저장합니다."""

    # 학습 이력이 없으면 그래프를 만들지 않습니다.
    if not history:
        # 함수를 종료합니다.
        return

    # 에포크 번호 목록을 추출합니다.
    epochs = [row["epoch"] for row in history]

    # 학습 손실 목록을 추출합니다.
    train_losses = [row["train_loss"] for row in history]

    # 검증 손실 목록을 추출합니다.
    val_losses = [row["val_loss"] for row in history]

    # 학습 정확도 목록을 추출합니다.
    train_accs = [row["train_accuracy"] for row in history]

    # 검증 정확도 목록을 추출합니다.
    val_accs = [row["val_accuracy"] for row in history]

    # 가로 10인치, 세로 8인치 그림을 생성합니다.
    plt.figure(figsize=(10, 8))

    # 손실 그래프를 그릴 첫 번째 영역을 선택합니다.
    plt.subplot(2, 1, 1)

    # 학습 손실 곡선을 그립니다.
    plt.plot(epochs, train_losses, label="Train Loss")

    # 검증 손실 곡선을 그립니다.
    plt.plot(epochs, val_losses, label="Validation Loss")

    # 손실 그래프 제목을 설정합니다.
    plt.title("Loss Curve")

    # 범례를 표시합니다.
    plt.legend()

    # 격자를 표시합니다.
    plt.grid(True)

    # 정확도 그래프를 그릴 두 번째 영역을 선택합니다.
    plt.subplot(2, 1, 2)

    # 학습 정확도 곡선을 그립니다.
    plt.plot(epochs, train_accs, label="Train Accuracy")

    # 검증 정확도 곡선을 그립니다.
    plt.plot(epochs, val_accs, label="Validation Accuracy")

    # 정확도 그래프 제목을 설정합니다.
    plt.title("Accuracy Curve")

    # 범례를 표시합니다.
    plt.legend()

    # 격자를 표시합니다.
    plt.grid(True)

    # 그래프 요소가 겹치지 않도록 여백을 조절합니다.
    plt.tight_layout()

    # 완성된 학습 곡선을 이미지 파일로 저장합니다.
    plt.savefig(output_path, dpi=150)

    # 그림 객체를 닫아 메모리를 해제합니다.
    plt.close()


def train_loop(config, bundle: DataBundle, model, optimizer, scheduler, early_stopping, start_epoch, end_epoch, best_val_loss, history):
    """신규 학습과 재개 학습에서 공통으로 사용하는 에포크 반복입니다."""

    # CPU 또는 CUDA 장치를 선택합니다.
    device = get_device()

    # 모델을 선택된 장치로 이동합니다.
    model = model.to(device)

    # 다중 클래스 분류용 교차 엔트로피 손실 함수를 생성합니다.
    criterion = nn.CrossEntropyLoss()

    # 실제 학습 장치를 출력합니다.
    print(f"\n학습 장치: {device}")

    # 지정한 시작 에포크부터 종료 에포크까지 반복합니다.
    for epoch in range(start_epoch, end_epoch + 1):
        # 학습 데이터 한 에포크를 실행합니다.
        train_loss, train_accuracy = run_epoch(model, bundle.train_loader, criterion, device, optimizer)

        # 검증 데이터 한 에포크를 실행합니다.
        val_loss, val_accuracy = run_epoch(model, bundle.val_loader, criterion, device, optimizer=None)

        # 현재 검증 손실에 따라 학습률 스케줄러를 갱신합니다.
        scheduler.step(val_loss)

        # 현재 실제 학습률을 가져옵니다.
        current_lr = optimizer.param_groups[0]["lr"]

        # 현재 에포크 결과를 사전으로 구성합니다.
        row = {
            "epoch": epoch,
            "train_loss": train_loss,
            "train_accuracy": train_accuracy,
            "val_loss": val_loss,
            "val_accuracy": val_accuracy,
            "learning_rate": current_lr,
        }

        # 현재 에포크 결과를 전체 이력에 추가합니다.
        history.append(row)

        # 현재 에포크의 주요 결과를 출력합니다.
        print(
            f"Epoch {epoch:03d} | "
            f"Train Loss {train_loss:.6f} | Train Acc {train_accuracy * 100:6.2f}% | "
            f"Val Loss {val_loss:.6f} | Val Acc {val_accuracy * 100:6.2f}% | LR {current_lr:.8f}"
        )

        # 현재 검증 손실이 최적값보다 낮은지 검사합니다.
        if val_loss < best_val_loss:
            # 최적 검증 손실을 갱신합니다.
            best_val_loss = val_loss

            # 현재 모델을 최적 모델 파일로 저장합니다.
            save_best_model(config, model, bundle.class_names, best_val_loss)

            # 최적 모델 저장 사실을 출력합니다.
            print(f"  → 최적 모델 저장: {config.best_model_path}")

        # 매 에포크 종료 시 전체 학습 상태를 체크포인트로 저장합니다.
        save_checkpoint(
            config,
            model,
            optimizer,
            scheduler,
            early_stopping,
            epoch,
            best_val_loss,
            history,
            bundle.class_names,
        )

        # 에포크별 학습 이력을 CSV로 저장합니다.
        save_history(history, config.history_path)

        # 학습 곡선을 PNG로 저장합니다.
        plot_history(history, config.curve_path)

        # 검증 손실이 장기간 개선되지 않았는지 검사합니다.
        if early_stopping.step(val_loss):
            # 조기 종료 사유를 출력합니다.
            print(f"\n조기 종료: {config.early_stopping_patience}회 연속 검증 손실 미개선")
            # 에포크 반복을 중단합니다.
            break

    # 학습된 모델과 이력을 반환합니다.
    return model, history


def train_new_model(config: Config) -> None:
    """새 모델을 생성하여 처음부터 학습합니다."""

    # 신규 학습 제목을 출력합니다.
    print("\n[CNN 신규 학습]")

    # 재현성을 위해 난수 시드를 다시 고정합니다.
    set_seed(config.seed)

    # 학습, 검증, 테스트 DataLoader를 생성합니다.
    bundle = prepare_dataloaders(config)

    # 데이터셋 클래스 수에 맞는 CNN 모델을 생성합니다.
    model = ImageClassifierCNN(num_classes=len(bundle.class_names))

    # AdamW 옵티마이저를 생성합니다.
    optimizer = optim.AdamW(
        model.parameters(),
        lr=config.learning_rate,
        weight_decay=config.weight_decay,
    )

    # 검증 손실이 정체되면 학습률을 절반으로 줄이는 스케줄러를 생성합니다.
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer,
        mode="min",
        factor=0.5,
        patience=2,
    )

    # 검증 손실 기반 조기 종료 객체를 생성합니다.
    early_stopping = EarlyStopping(
        patience=config.early_stopping_patience,
        min_delta=config.early_stopping_min_delta,
    )

    # 아직 최적 손실이 없으므로 무한대로 초기화합니다.
    best_val_loss = float("inf")

    # 비어 있는 학습 이력 목록을 생성합니다.
    history = []

    # 공통 학습 반복을 실행합니다.
    train_loop(
        config,
        bundle,
        model,
        optimizer,
        scheduler,
        early_stopping,
        start_epoch=1,
        end_epoch=config.epochs,
        best_val_loss=best_val_loss,
        history=history,
    )

    # 학습 완료 메시지를 출력합니다.
    print("\n학습 완료")

    # 최적 모델 경로를 출력합니다.
    print(f"최적 모델: {config.best_model_path}")

    # 마지막 체크포인트 경로를 출력합니다.
    print(f"체크포인트: {config.checkpoint_path}")


def resume_training(config: Config) -> None:
    """마지막 체크포인트에서 모델과 학습 상태를 복원합니다."""

    # 재개 학습 제목을 출력합니다.
    print("\n[체크포인트에서 학습 재개]")

    # 체크포인트 파일 존재 여부를 검사합니다.
    if not config.checkpoint_path.exists():
        # 체크포인트가 없으면 신규 학습을 먼저 실행하도록 오류를 발생시킵니다.
        raise FileNotFoundError("last_checkpoint.pt가 없습니다. 먼저 신규 학습을 실행하세요.")

    # 같은 데이터 분할을 재현하도록 난수 시드를 고정합니다.
    set_seed(config.seed)

    # 현재 데이터셋의 DataLoader를 생성합니다.
    bundle = prepare_dataloaders(config)

    # 체크포인트 파일을 CPU 메모리로 불러옵니다.
    checkpoint = torch.load(config.checkpoint_path, map_location="cpu", weights_only=False)

    # 체크포인트의 클래스 목록이 현재 데이터셋과 같은지 검사합니다.
    if checkpoint["class_names"] != bundle.class_names:
        # 클래스 구성이 다르면 모델 출력 계층이 호환되지 않으므로 오류를 발생시킵니다.
        raise ValueError("체크포인트와 현재 데이터셋의 클래스 구성이 다릅니다.")

    # 현재 클래스 수에 맞는 CNN 모델을 생성합니다.
    model = ImageClassifierCNN(num_classes=len(bundle.class_names))

    # 저장된 모델 가중치를 복원합니다.
    model.load_state_dict(checkpoint["model_state_dict"])

    # 신규 학습과 동일한 AdamW 옵티마이저를 생성합니다.
    optimizer = optim.AdamW(
        model.parameters(),
        lr=config.learning_rate,
        weight_decay=config.weight_decay,
    )

    # 저장된 옵티마이저 상태를 복원합니다.
    optimizer.load_state_dict(checkpoint["optimizer_state_dict"])

    # 동일한 학습률 스케줄러를 생성합니다.
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer,
        mode="min",
        factor=0.5,
        patience=2,
    )

    # 저장된 스케줄러 상태를 복원합니다.
    scheduler.load_state_dict(checkpoint["scheduler_state_dict"])

    # 조기 종료 객체를 생성합니다.
    early_stopping = EarlyStopping(
        patience=config.early_stopping_patience,
        min_delta=config.early_stopping_min_delta,
    )

    # 저장된 조기 종료 상태를 복원합니다.
    early_stopping.load_state_dict(checkpoint["early_stopping_state"])

    # 마지막 에포크 다음 번호를 시작 에포크로 설정합니다.
    start_epoch = checkpoint["epoch"] + 1

    # 추가 학습 횟수를 반영해 종료 에포크를 계산합니다.
    end_epoch = checkpoint["epoch"] + config.resume_epochs

    # 저장된 학습 이력을 복원합니다.
    history = checkpoint.get("history", [])

    # 재개 학습 에포크 범위를 출력합니다.
    print(f"{start_epoch} 에포크부터 {end_epoch} 에포크까지 추가 학습합니다.")

    # 공통 학습 반복을 실행합니다.
    train_loop(
        config,
        bundle,
        model,
        optimizer,
        scheduler,
        early_stopping,
        start_epoch,
        end_epoch,
        checkpoint["best_val_loss"],
        history,
    )

    # 재개 학습 완료 메시지를 출력합니다.
    print("\n추가 학습 완료")


def calculate_confusion_matrix(targets, predictions, num_classes):
    """실제 클래스와 예측 클래스로 혼동행렬을 생성합니다."""

    # 클래스 수에 맞는 0 행렬을 생성합니다.
    matrix = torch.zeros((num_classes, num_classes), dtype=torch.int64)

    # 실제값과 예측값을 한 쌍씩 반복합니다.
    for target, prediction in zip(targets, predictions):
        # 실제 클래스 행과 예측 클래스 열의 값을 1 증가시킵니다.
        matrix[target, prediction] += 1

    # 완성된 혼동행렬을 반환합니다.
    return matrix


def evaluate_best_model(config: Config) -> None:
    """저장된 최적 모델을 테스트 데이터셋에서 평가합니다."""

    # 테스트 평가 제목을 출력합니다.
    print("\n[저장된 최적 모델 테스트 평가]")

    # 최적 모델 파일 존재 여부를 검사합니다.
    if not config.best_model_path.exists():
        # 모델이 없으면 먼저 학습을 실행하도록 오류를 발생시킵니다.
        raise FileNotFoundError("best_model.pt가 없습니다. 먼저 모델을 학습하세요.")

    # 같은 테스트 분할을 재현하도록 난수 시드를 고정합니다.
    set_seed(config.seed)

    # 테스트 DataLoader를 포함한 데이터 묶음을 생성합니다.
    bundle = prepare_dataloaders(config)

    # 저장된 최적 모델 데이터를 CPU 메모리로 불러옵니다.
    saved = torch.load(config.best_model_path, map_location="cpu", weights_only=False)

    # 저장된 클래스 구성과 현재 클래스 구성이 같은지 검사합니다.
    if saved["class_names"] != bundle.class_names:
        # 클래스 불일치 시 잘못된 평가를 막기 위해 오류를 발생시킵니다.
        raise ValueError("저장 모델과 현재 데이터셋의 클래스 구성이 다릅니다.")

    # 저장된 클래스 수에 맞는 CNN 모델을 생성합니다.
    model = ImageClassifierCNN(num_classes=saved["num_classes"])

    # 저장된 최적 가중치를 복원합니다.
    model.load_state_dict(saved["model_state_dict"])

    # CPU 또는 CUDA 장치를 선택합니다.
    device = get_device()

    # 모델을 선택된 장치로 이동합니다.
    model = model.to(device)

    # 모델을 평가 모드로 설정합니다.
    model.eval()

    # 교차 엔트로피 손실 함수를 생성합니다.
    criterion = nn.CrossEntropyLoss()

    # 전체 테스트 손실을 0으로 초기화합니다.
    total_loss = 0.0

    # 전체 정답 수를 0으로 초기화합니다.
    total_correct = 0

    # 전체 테스트 샘플 수를 0으로 초기화합니다.
    total_samples = 0

    # 실제 레이블 전체를 저장할 목록을 생성합니다.
    targets = []

    # 예측 레이블 전체를 저장할 목록을 생성합니다.
    predictions_all = []

    # 평가 중에는 기울기 계산을 비활성화합니다.
    with torch.no_grad():
        # 테스트 미니배치를 순서대로 반복합니다.
        for images, labels in bundle.test_loader:
            # 이미지를 선택된 장치로 이동합니다.
            images = images.to(device)

            # 레이블을 선택된 장치로 이동합니다.
            labels = labels.to(device)

            # 모델 순전파로 클래스 로짓을 계산합니다.
            logits = model(images)

            # 테스트 손실을 계산합니다.
            loss = criterion(logits, labels)

            # 가장 큰 로짓을 가진 클래스를 예측값으로 선택합니다.
            predictions = torch.argmax(logits, dim=1)

            # 샘플 수를 반영한 손실을 누적합니다.
            total_loss += loss.item() * images.size(0)

            # 정답 수를 누적합니다.
            total_correct += (predictions == labels).sum().item()

            # 처리한 샘플 수를 누적합니다.
            total_samples += images.size(0)

            # 실제 레이블을 CPU 목록으로 변환하여 저장합니다.
            targets.extend(labels.cpu().tolist())

            # 예측 레이블을 CPU 목록으로 변환하여 저장합니다.
            predictions_all.extend(predictions.cpu().tolist())

    # 전체 테스트 평균 손실을 계산합니다.
    test_loss = total_loss / total_samples

    # 전체 테스트 정확도를 계산합니다.
    test_accuracy = total_correct / total_samples

    # 혼동행렬을 계산합니다.
    matrix = calculate_confusion_matrix(targets, predictions_all, len(bundle.class_names))

    # 테스트 평균 손실을 출력합니다.
    print(f"\n테스트 손실: {test_loss:.6f}")

    # 테스트 정확도를 백분율로 출력합니다.
    print(f"테스트 정확도: {test_accuracy * 100:.2f}%")

    # 혼동행렬 설명을 출력합니다.
    print("\n혼동행렬: 실제 클래스=행, 예측 클래스=열")

    # 혼동행렬 값을 출력합니다.
    print(matrix)

    # 클래스별 평가 지표 제목을 출력합니다.
    print("\n클래스별 Precision / Recall / F1")

    # 각 클래스 인덱스와 이름을 순서대로 반복합니다.
    for index, class_name in enumerate(bundle.class_names):
        # 현재 클래스의 True Positive를 계산합니다.
        tp = matrix[index, index].item()

        # 현재 클래스로 잘못 예측한 False Positive를 계산합니다.
        fp = matrix[:, index].sum().item() - tp

        # 현재 클래스를 다른 클래스로 예측한 False Negative를 계산합니다.
        fn = matrix[index, :].sum().item() - tp

        # 0으로 나누는 문제를 방지하며 Precision을 계산합니다.
        precision = tp / (tp + fp) if tp + fp > 0 else 0.0

        # 0으로 나누는 문제를 방지하며 Recall을 계산합니다.
        recall = tp / (tp + fn) if tp + fn > 0 else 0.0

        # Precision과 Recall을 이용하여 F1 점수를 계산합니다.
        f1 = 2 * precision * recall / (precision + recall) if precision + recall > 0 else 0.0

        # 현재 클래스의 지표를 출력합니다.
        print(f"{class_name:>15s} | P {precision:.4f} | R {recall:.4f} | F1 {f1:.4f}")
