# app/train.py
"""학습·평가·시각화·성능 지표를 담당하는 모듈."""

from __future__ import annotations

import os, pickle, random
from typing import Dict, Tuple

import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams["font.family"] = "Malgun Gothic"  # Windows
matplotlib.rcParams["axes.unicode_minus"] = False

import torch
torch.set_num_threads(1)
torch.backends.mkldnn.enabled = False

from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, ConfusionMatrixDisplay
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

from app.config import Config
from app.data import load_sample_data, load_crawled_data
from app.model import TextLSTMClassifier
from app.preprocess import build_vocab, clean_text, encode_labels, pad_sequences, texts_to_sequences


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def plot_history(train_losses: list, val_losses: list, val_accuracies: list) -> None:
    """Epoch별 손실·정확도 그래프를 저장한다."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))

    ax1.plot(train_losses, label="Train Loss")
    ax1.plot(val_losses, label="Val Loss")
    ax1.set_title("Epoch별 손실")
    ax1.set_xlabel("Epoch")
    ax1.set_ylabel("Loss")
    ax1.legend()

    ax2.plot(val_accuracies, label="Val Accuracy", color="green")
    ax2.set_title("Epoch별 정확도")
    ax2.set_xlabel("Epoch")
    ax2.set_ylabel("Accuracy")
    ax2.legend()

    os.makedirs("data", exist_ok=True)
    plt.tight_layout()
    plt.savefig("data/training_history.png")
    plt.show()
    print("✅ 그래프 저장 완료: data/training_history.png")


def plot_confusion_matrix(all_targets: list, all_preds: list, labels: list) -> None:
    """혼동 행렬을 시각화해서 저장한다."""
    cm = confusion_matrix(all_targets, all_preds)
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=labels)
    fig, ax = plt.subplots(figsize=(8, 6))
    disp.plot(ax=ax, colorbar=False)
    ax.set_title("혼동 행렬 (Confusion Matrix)")
    plt.tight_layout()
    plt.savefig("data/confusion_matrix.png")
    plt.show()
    print("✅ 혼동 행렬 저장 완료: data/confusion_matrix.png")


def train_model(config: Config, use_crawling: bool = False) -> Tuple[TextLSTMClassifier, Dict]:
    """네이버 뉴스 데이터로 LSTM 분류 모델을 학습하고 시각화 결과를 저장한다."""

    set_seed(config.random_state)

    # 데이터 로드: 크롤링 or 샘플
    if use_crawling:
        print("🌐 네이버 뉴스 크롤링 중...")
        raw_texts, labels = load_crawled_data()
        if len(raw_texts) < 10:                          # 크롤링 실패 시 샘플로 폴백한다.
            print("⚠️ 크롤링 데이터 부족, 샘플 데이터로 전환합니다.")
            raw_texts, labels = load_sample_data()
    else:
        raw_texts, labels = load_sample_data()

    cleaned_texts = [clean_text(text) for text in raw_texts]
    pairs = [(t, l) for t, l in zip(cleaned_texts, labels) if t.strip()]  # 빈 문자열 제거
    cleaned_texts, labels = zip(*pairs)
    vocab = build_vocab(cleaned_texts, config.max_vocab)
    sequences = texts_to_sequences(cleaned_texts, vocab)
    x = pad_sequences(sequences, config.max_len)
    y, label_to_id, id_to_label = encode_labels(labels)

    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=config.test_size, random_state=config.random_state, stratify=y
    )

    train_loader = DataLoader(TensorDataset(torch.tensor(x_train), torch.tensor(y_train)),
                              batch_size=config.batch_size, shuffle=True)
    test_loader  = DataLoader(TensorDataset(torch.tensor(x_test), torch.tensor(y_test)),
                              batch_size=config.batch_size)

    model = TextLSTMClassifier(
        vocab_size=len(vocab), embed_dim=config.embed_dim, hidden_dim=config.hidden_dim,
        num_classes=len(label_to_id))
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=config.learning_rate)
    scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=5, gamma=0.5)
    # StepLR: 5 epoch마다 학습률을 절반으로 줄여 후반부 학습을 안정화한다.

    train_losses, val_losses, val_accuracies = [], [], []

    for epoch in range(1, config.epochs + 1):
        # ── 학습 ──
        model.train()
        total_loss = 0.0
        for batch_x, batch_y in train_loader:
            optimizer.zero_grad()
            loss = criterion(model(batch_x), batch_y)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)  # 기울기 폭발을 방지한다.
            optimizer.step()
            total_loss += loss.item()
        avg_train_loss = total_loss / len(train_loader)
        train_losses.append(avg_train_loss)

        # ── 검증 ──
        model.eval()
        val_loss, preds, targets = 0.0, [], []
        with torch.no_grad():
            for batch_x, batch_y in test_loader:
                logits = model(batch_x)
                val_loss += criterion(logits, batch_y).item()
                preds.extend(torch.argmax(logits, dim=1).tolist())
                targets.extend(batch_y.tolist())
        avg_val_loss = val_loss / len(test_loader)
        acc = accuracy_score(targets, preds)
        val_losses.append(avg_val_loss)
        val_accuracies.append(acc)
        scheduler.step()

        print(f"Epoch {epoch:02d}/{config.epochs} "
              f"| train_loss: {avg_train_loss:.4f} "
              f"| val_loss: {avg_val_loss:.4f} "
              f"| val_acc: {acc:.4f}")

    # ── 최종 평가 ──
    print("\n📊 최종 평가 리포트")
    label_names = [id_to_label[i] for i in range(len(id_to_label))]
    print(classification_report(targets, preds, target_names=label_names, zero_division=0))

    plot_history(train_losses, val_losses, val_accuracies)
    plot_confusion_matrix(targets, preds, label_names)

    # ── 저장 ──
    os.makedirs(os.path.dirname(config.model_path), exist_ok=True)
    torch.save(model.state_dict(), config.model_path)
    with open(config.model_path.replace(".pt", "_meta.pkl"), "wb") as f:
        pickle.dump({"vocab": vocab, "label_to_id": label_to_id,
                     "id_to_label": id_to_label, "config": config}, f)

    return model, {"vocab": vocab, "label_to_id": label_to_id,
                   "id_to_label": id_to_label, "accuracy": val_accuracies[-1]}