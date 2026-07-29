# CNN 실제 이미지 분류 PyCharm 콘솔 프로젝트

이 프로젝트는 실제 이미지 분류 학습의 전체 흐름을 PyCharm 콘솔에서 확인할 수 있도록 구현했습니다.

## 구현 기능

- `ImageFolder` 방식 실제 이미지 로딩
- 실제 이미지가 없을 때 `FakeData`로 코드 실행 확인
- 학습 70%, 검증 15%, 테스트 15% 분리
- 학습 데이터에만 데이터 증강 적용
- 검증 손실을 이용한 최적 모델 선택
- 테스트 데이터 최종 평가
- 최적 모델 저장
- 매 에포크 체크포인트 저장
- 체크포인트에서 모델·옵티마이저·스케줄러 복원
- 조기 종료
- 학습률 자동 감소
- 학습 이력 CSV 저장
- 손실 및 정확도 곡선 저장
- 혼동행렬, Precision, Recall, F1-score 출력
- 단일 이미지 추론

## 프로젝트 구조

```text
cnn_image_classification_console_project/
├── main.py
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── data.py
│   ├── model.py
│   ├── trainer.py
│   ├── predict.py
│   └── utils.py
├── data/
│   └── images/
├── artifacts/
├── logs/
├── requirements.txt
├── run.bat
├── run.sh
└── .gitignore
```

## 실제 이미지 폴더 구성

```text
data/images/
├── cat/
│   ├── cat_001.jpg
│   └── cat_002.jpg
└── dog/
    ├── dog_001.jpg
    └── dog_002.jpg
```

하위 폴더 이름이 클래스 이름으로 사용됩니다.

## 권장 환경

- Python 3.11
- PyCharm
- Windows 10 또는 Windows 11
- CPU 실행 가능
- GPU는 필수 아님

## 설치

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

CUDA GPU용 PyTorch가 필요한 경우에는 사용 중인 CUDA 환경에 맞는 PyTorch 설치 명령을 적용하십시오.

## 실행

```bash
python main.py
```

## 메뉴

```text
1. 데이터셋 구조와 클래스 정보 확인
2. 학습/검증/테스트 분할 결과 확인
3. 데이터 증강 미리보기 저장
4. CNN 신규 학습
5. 저장된 최적 모델 테스트 평가
6. 단일 이미지 분류
7. 체크포인트에서 학습 재개
8. 실행 환경 확인
0. 프로그램 종료
```

## 데이터 분리 원칙

- 학습 데이터는 모델 가중치 갱신에 사용합니다.
- 검증 데이터는 최적 모델 선택, 학습률 조정, 조기 종료에 사용합니다.
- 테스트 데이터는 학습 완료 후 최종 일반화 성능 평가에만 사용합니다.
- 테스트 데이터로 모델을 선택하면 성능 평가가 왜곡될 수 있습니다.

## 데이터 증강

학습 데이터에만 다음 증강을 적용합니다.

```text
RandomResizedCrop
RandomHorizontalFlip
RandomRotation
ColorJitter
Normalize
```

검증과 테스트에는 무작위 증강을 적용하지 않습니다.

## 저장 파일

```text
artifacts/best_model.pt
artifacts/last_checkpoint.pt
artifacts/previews/augmentation_preview.png
logs/training_history.csv
logs/training_curves.png
```

## 조기 종료

기본값은 다음과 같습니다.

```text
patience = 5
min_delta = 0.0001
```

검증 손실이 5회 연속 충분히 개선되지 않으면 학습을 중단합니다.

## 설정 변경

`src/config.py`에서 다음 값을 변경할 수 있습니다.

```python
image_size = 128
batch_size = 16
epochs = 30
learning_rate = 0.001
train_ratio = 0.70
val_ratio = 0.15
test_ratio = 0.15
```

## FakeData 안내

`data/images`에 실제 클래스 폴더가 없으면 자동으로 FakeData를 사용합니다. FakeData는 코드 흐름 검증용이며 분류 정확도 자체에는 실제 의미가 없습니다.
