# CNN 구조와 연산 원리 학습용 콘솔 프로젝트

이 프로젝트는 PyCharm에서 실행하면서 CNN의 구조와 연산 원리를 단계별로 확인할 수 있도록 구성한 콘솔 애플리케이션입니다.

## 주요 실습

1. CNN 전체 구조 확인
2. NumPy 기반 2차원 합성곱 연산
3. 스트라이드와 패딩에 따른 출력 크기 비교
4. ReLU 활성화 함수 연산
5. 최대 풀링과 평균 풀링 연산
6. RGB 형태의 다중 채널 합성곱 연산
7. PyTorch CNN 순전파와 계층별 텐서 크기 확인
8. 합성곱 계층과 완전연결 계층의 파라미터 수 계산
9. 합성 이미지 기반 CNN 학습과 역전파 확인

## 프로젝트 구조

```text
cnn_console_learning_project/
├── main.py
├── demos/
│   ├── __init__.py
│   ├── cnn_structure_demo.py
│   ├── convolution_demo.py
│   ├── output_size_demo.py
│   ├── activation_demo.py
│   ├── pooling_demo.py
│   ├── multichannel_demo.py
│   ├── pytorch_forward_demo.py
│   ├── parameter_demo.py
│   └── training_demo.py
├── requirements.txt
├── run.bat
├── run.sh
└── .gitignore
```

## 권장 환경

- Python 3.11
- PyCharm
- Windows 10 또는 Windows 11
- CPU 실행 가능
- GPU는 필수 아님

## PyCharm에서 실행하는 방법

### 1. 프로젝트 열기

압축을 해제한 후 PyCharm에서 `cnn_console_learning_project` 폴더를 엽니다.

### 2. 가상환경 생성

PyCharm 메뉴에서 다음 순서로 설정합니다.

```text
File
→ Settings
→ Project
→ Python Interpreter
→ Add Interpreter
→ Add Local Interpreter
→ Virtualenv Environment
```

Python 3.11을 선택하여 `.venv` 가상환경을 생성합니다.

### 3. 패키지 설치

PyCharm Terminal에서 다음 명령을 실행합니다.

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

PyTorch 설치가 운영체제나 CUDA 환경과 맞지 않는 경우에는 PyTorch 공식 설치 명령을 사용하십시오. 이 프로젝트는 CPU 버전으로도 실행할 수 있습니다.

### 4. 프로그램 실행

```bash
python main.py
```

또는 PyCharm에서 `main.py`를 마우스 오른쪽 버튼으로 클릭한 후 `Run 'main'`을 선택합니다.

## 메뉴별 학습 포인트

### 메뉴 2: 합성곱 연산

커널이 입력 위를 이동하면서 다음 과정을 반복합니다.

```text
입력 영역 선택
→ 커널과 원소별 곱셈
→ 모든 값 합산
→ 특성 맵에 저장
```

### 메뉴 3: 출력 크기

다음 공식을 사용합니다.

```text
출력 크기
= floor((입력 크기 - 커널 크기 + 2×패딩) / 스트라이드) + 1
```

### 메뉴 6: 다중 채널 합성곱

RGB 입력에서는 커널도 입력 채널 수와 동일한 깊이를 가집니다.

```text
R 채널 계산
+ G 채널 계산
+ B 채널 계산
+ 편향
= 출력 특성 값
```

### 메뉴 7: 순전파

PyTorch 텐서 크기가 다음처럼 변화하는 것을 확인합니다.

```text
[배치, 1, 28, 28]
→ [배치, 8, 28, 28]
→ [배치, 8, 14, 14]
→ [배치, 16, 14, 14]
→ [배치, 16, 7, 7]
→ [배치, 784]
→ [배치, 10]
```

### 메뉴 9: 역전파와 학습

외부 데이터 다운로드 없이 다음 두 클래스를 생성합니다.

- 클래스 0: 세로선 이미지
- 클래스 1: 가로선 이미지

학습 과정에서 다음 흐름을 확인할 수 있습니다.

```text
순전파
→ 교차 엔트로피 손실 계산
→ loss.backward()
→ 커널 기울기 계산
→ optimizer.step()
→ 커널 갱신
```

## 참고

모든 예제는 CNN의 원리를 쉽게 확인하기 위한 교육용 코드입니다. 실제 이미지 분류 프로젝트에서는 데이터 분리, 검증, 테스트, 모델 저장, 체크포인트, 조기 종료, 데이터 증강 등의 기능을 추가해야 합니다.
