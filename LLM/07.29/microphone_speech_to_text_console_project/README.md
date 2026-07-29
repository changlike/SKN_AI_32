# 마이크 음성 텍스트 변환 PyCharm 콘솔 프로젝트

마이크에서 전달받은 음성을 WAV 파일로 저장하고 Faster-Whisper를 사용하여 텍스트로 변환하는 콘솔 프로젝트입니다.

## 주요 기능

- 오디오 입력 장치 목록 출력
- 기본 마이크 또는 사용자가 지정한 마이크 선택
- 지정 시간 동안 녹음
- Enter 키를 누를 때까지 녹음
- 16kHz, 16비트 PCM WAV 저장
- Faster-Whisper 기반 로컬 음성 인식
- 한국어 음성 인식
- 음성 구간별 시작·종료 시간 출력
- 전체 변환 텍스트 출력
- TXT 및 JSON 결과 저장
- 기존 WAV 파일 변환
- CPU 및 NVIDIA GPU 설정 지원

## 프로젝트 구조

```text
microphone_speech_to_text_console_project/
├── main.py
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── audio_recorder.py
│   ├── transcriber.py
│   └── result_writer.py
├── recordings/
├── results/
├── requirements.txt
├── .env.example
├── run.bat
├── run.sh
└── .gitignore
```

## 권장 실행 환경

- Windows 10 또는 Windows 11
- Python 3.11
- PyCharm
- 정상적으로 연결된 마이크
- 최초 모델 다운로드를 위한 인터넷 연결
- 이후 다운로드된 모델은 로컬 캐시에서 사용 가능

## PyCharm 실행 방법

### 1. 프로젝트 열기

압축 파일을 해제한 후 PyCharm에서 다음 폴더를 엽니다.

```text
microphone_speech_to_text_console_project
```

### 2. 가상환경 생성

```text
File
→ Settings
→ Project
→ Python Interpreter
→ Add Interpreter
→ Add Local Interpreter
→ Virtualenv
```

Python 3.11을 선택합니다.

### 3. 패키지 설치

PyCharm Terminal에서 실행합니다.

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. 프로그램 실행

```bash
python main.py
```

또는 `main.py`를 마우스 오른쪽 버튼으로 클릭한 후 `Run 'main'`을 선택합니다.

## 메뉴

```text
1. 오디오 입력 장치 목록 확인
2. 지정 시간 동안 녹음 후 텍스트 변환
3. Enter 키를 누를 때까지 녹음 후 텍스트 변환
4. 기존 WAV 파일 텍스트 변환
5. 현재 설정 정보 확인
0. 프로그램 종료
```

## 첫 실행 시 모델 다운로드

기본 모델은 `small`입니다.

처음 변환을 실행하면 Faster-Whisper가 모델 파일을 다운로드합니다. 모델 크기에 따라 다운로드 시간과 저장 공간이 달라집니다.

낮은 사양의 CPU 환경에서는 다음 설정을 권장합니다.

```text
WHISPER_MODEL_SIZE=base
WHISPER_DEVICE=cpu
WHISPER_COMPUTE_TYPE=int8
```

더 높은 정확도가 필요하고 메모리가 충분하면 다음 설정을 사용할 수 있습니다.

```text
WHISPER_MODEL_SIZE=medium
WHISPER_DEVICE=cpu
WHISPER_COMPUTE_TYPE=int8
```

NVIDIA GPU 환경의 예시는 다음과 같습니다.

```text
WHISPER_MODEL_SIZE=medium
WHISPER_DEVICE=cuda
WHISPER_COMPUTE_TYPE=float16
```

현재 프로젝트는 `.env` 라이브러리를 사용하지 않으므로 PyCharm 실행 구성의 환경 변수에 값을 등록하거나 운영체제 환경 변수로 설정합니다.

## Windows 마이크 권한 확인

마이크가 동작하지 않으면 Windows에서 다음을 확인합니다.

```text
설정
→ 개인정보 및 보안
→ 마이크
→ 마이크 액세스 켬
→ 데스크톱 앱에서 마이크 액세스 켬
```

## 입력 장치 선택

먼저 메뉴 1을 실행합니다.

```text
0: Microsoft Sound Mapper - Input
1: Microphone Array
2: USB Microphone
```

녹음 메뉴에서 원하는 입력 장치 번호를 입력합니다. Enter만 누르면 운영체제 기본 입력 장치를 사용합니다.

## 저장 결과

녹음된 WAV 파일:

```text
recordings/recording_날짜_시간.wav
```

변환된 TXT 파일:

```text
results/transcription_날짜_시간.txt
```

구조화된 JSON 파일:

```text
results/transcription_날짜_시간.json
```

## 음성 인식 처리 흐름

```text
마이크
↓
sounddevice 입력 스트림
↓
16kHz 모노 PCM 데이터
↓
WAV 파일 저장
↓
Faster-Whisper 모델
↓
언어 및 음성 구간 분석
↓
전체 텍스트 생성
↓
TXT와 JSON 저장
```

## 자주 발생하는 오류

### PortAudio 또는 입력 장치 오류

메뉴 1에서 입력 장치 번호를 확인한 후 녹음 메뉴에서 해당 번호를 입력합니다.

USB 마이크를 새로 연결했다면 프로그램을 다시 실행합니다.

### Invalid sample rate 오류

일부 마이크가 16kHz 녹음을 직접 지원하지 않을 수 있습니다.

`src/config.py`의 다음 값을 장치 기본 주파수로 변경할 수 있습니다.

```python
sample_rate = 44100
```

Faster-Whisper는 저장된 파일을 읽을 때 필요한 샘플링 변환을 내부 처리할 수 있습니다.

### 모델 로드가 느린 경우

최초 실행에서는 모델을 다운로드하므로 시간이 필요합니다. 이후 실행에서는 캐시된 모델을 사용합니다.

### CUDA 오류

NVIDIA GPU, 드라이버 또는 CUDA 라이브러리가 준비되지 않았다면 CPU 설정으로 변경합니다.

```text
WHISPER_DEVICE=cpu
WHISPER_COMPUTE_TYPE=int8
```

## 개인정보 주의

음성 파일과 변환 텍스트는 프로젝트의 `recordings`, `results` 폴더에 저장됩니다. 개인정보나 민감한 대화를 녹음한 경우 파일 접근 권한과 삭제 정책을 직접 관리해야 합니다.
