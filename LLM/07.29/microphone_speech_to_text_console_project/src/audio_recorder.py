"""
sounddevice를 이용하여 마이크 음성을 녹음하고 WAV 파일로 저장합니다.
"""

# Enter 종료 방식 녹음에서 오디오 블록을 안전하게 전달하기 위해 queue를 가져옵니다.
import queue

# WAV 파일을 표준 PCM 형식으로 저장하기 위해 wave 모듈을 가져옵니다.
import wave

# 녹음 파일명에 날짜와 시간을 포함하기 위해 datetime을 가져옵니다.
from datetime import datetime

# 파일 경로 타입을 사용하기 위해 Path 클래스를 가져옵니다.
from pathlib import Path

# 녹음 배열을 결합하고 자료형을 처리하기 위해 NumPy를 가져옵니다.
import numpy as np

# 운영체제의 오디오 입력 장치에서 녹음하기 위해 sounddevice를 가져옵니다.
import sounddevice as sd

# 프로젝트 설정 타입을 가져옵니다.
from src.config import Config


def list_input_devices() -> None:
    """
    현재 컴퓨터에서 사용할 수 있는 오디오 입력 장치를 출력합니다.
    """

    # 장치 목록 출력 제목을 표시합니다.
    print("\n[오디오 입력 장치 목록]")

    # sounddevice가 인식한 모든 오디오 장치 정보를 가져옵니다.
    devices = sd.query_devices()

    # 운영체제의 기본 입력 및 출력 장치 번호를 가져옵니다.
    default_devices = sd.default.device

    # 기본 입력 장치 번호를 정수로 변환합니다.
    default_input_index = int(default_devices[0])

    # 전체 오디오 장치를 인덱스와 함께 반복합니다.
    for index, device in enumerate(devices):
        # 현재 장치가 입력 채널을 하나 이상 제공하는지 확인합니다.
        if int(device["max_input_channels"]) > 0:
            # 현재 장치가 기본 입력 장치인지 표시할 문자열을 결정합니다.
            default_mark = " [기본 입력]" if index == default_input_index else ""

            # 장치 번호, 이름, 최대 입력 채널과 기본 샘플링 주파수를 출력합니다.
            print(
                f"{index:2d}: {device['name']}{default_mark} | "
                f"입력 채널={int(device['max_input_channels'])} | "
                f"기본 샘플링={float(device['default_samplerate']):.0f}Hz"
            )


def _build_recording_path(config: Config) -> Path:
    """
    현재 시간을 이용하여 중복되지 않는 WAV 저장 경로를 생성합니다.
    """

    # 현재 날짜와 시간을 파일명에 사용할 문자열로 변환합니다.
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

    # recordings 폴더 아래에 녹음 WAV 파일 경로를 생성합니다.
    return config.recordings_dir / f"recording_{timestamp}.wav"


def _validate_input_device(
    config: Config,
    device_index: int | None,
) -> None:
    """
    선택한 입력 장치가 현재 녹음 설정을 지원하는지 검사합니다.
    """

    # 지정한 장치와 샘플링 주파수 및 채널 설정을 sounddevice에 검사하도록 요청합니다.
    sd.check_input_settings(
        device=device_index,
        samplerate=config.sample_rate,
        channels=config.channels,
        dtype=config.recording_dtype,
    )


def save_wav(
    file_path: Path,
    audio_data: np.ndarray,
    sample_rate: int,
    channels: int,
) -> None:
    """
    NumPy int16 오디오 배열을 PCM WAV 파일로 저장합니다.
    """

    # 저장할 오디오 배열이 int16이 아니면 안전하게 int16으로 변환합니다.
    if audio_data.dtype != np.int16:
        # WAV의 16비트 PCM 형식에 맞도록 자료형을 변환합니다.
        audio_data = audio_data.astype(np.int16)

    # WAV 파일을 바이너리 쓰기 모드로 엽니다.
    with wave.open(
        str(file_path),
        "wb",
    ) as wav_file:
        # WAV 파일의 채널 수를 설정합니다.
        wav_file.setnchannels(channels)

        # 16비트 PCM은 샘플당 2바이트이므로 샘플 너비를 2로 설정합니다.
        wav_file.setsampwidth(2)

        # WAV 파일의 초당 샘플 수를 설정합니다.
        wav_file.setframerate(sample_rate)

        # NumPy 오디오 배열을 바이트열로 변환하여 WAV 데이터로 기록합니다.
        wav_file.writeframes(audio_data.tobytes())


def record_for_seconds(
    config: Config,
    duration_seconds: float,
    device_index: int | None = None,
) -> Path:
    """
    지정한 시간 동안 마이크 음성을 녹음하고 WAV 경로를 반환합니다.
    """

    # 녹음 시간이 0보다 큰지 검사합니다.
    if duration_seconds <= 0:
        # 유효하지 않은 녹음 시간에 대한 예외를 발생시킵니다.
        raise ValueError("녹음 시간은 0초보다 커야 합니다.")

    # 지나치게 긴 실수 입력을 방지하기 위해 최대 녹음 시간을 검사합니다.
    if duration_seconds > config.max_recording_seconds:
        # 설정된 최대 시간을 초과했다는 예외를 발생시킵니다.
        raise ValueError(
            f"한 번의 녹음은 최대 {config.max_recording_seconds}초까지 가능합니다."
        )

    # 선택한 마이크 장치가 현재 설정을 지원하는지 검사합니다.
    _validate_input_device(
        config=config,
        device_index=device_index,
    )

    # 녹음할 전체 프레임 수를 초와 샘플링 주파수로 계산합니다.
    frame_count = int(duration_seconds * config.sample_rate)

    # 녹음 시작 안내를 출력합니다.
    print(f"\n{duration_seconds:.1f}초 동안 녹음합니다. 지금 말씀하세요.")

    # 지정한 프레임 수만큼 마이크 입력 녹음을 시작합니다.
    audio_data = sd.rec(
        frames=frame_count,
        samplerate=config.sample_rate,
        channels=config.channels,
        dtype=config.recording_dtype,
        device=device_index,
    )

    # 요청한 녹음이 모두 끝날 때까지 현재 스레드를 대기시킵니다.
    sd.wait()

    # 중복되지 않는 WAV 저장 경로를 생성합니다.
    output_path = _build_recording_path(config)

    # 녹음된 NumPy 배열을 WAV 파일로 저장합니다.
    save_wav(
        file_path=output_path,
        audio_data=audio_data,
        sample_rate=config.sample_rate,
        channels=config.channels,
    )

    # 녹음 완료와 저장 경로를 출력합니다.
    print(f"녹음 완료: {output_path}")

    # 저장된 WAV 파일 경로를 반환합니다.
    return output_path


def record_until_enter(
    config: Config,
    device_index: int | None = None,
) -> Path:
    """
    사용자가 Enter 키를 누를 때까지 마이크 입력을 스트리밍 방식으로 녹음합니다.
    """

    # 선택한 입력 장치가 현재 설정을 지원하는지 검사합니다.
    _validate_input_device(
        config=config,
        device_index=device_index,
    )

    # 오디오 콜백에서 메인 코드로 녹음 블록을 전달할 큐를 생성합니다.
    audio_queue: queue.Queue[np.ndarray] = queue.Queue()

    # 큐에서 가져온 모든 오디오 블록을 저장할 리스트를 생성합니다.
    audio_blocks: list[np.ndarray] = []

    # 최대 녹음 프레임 수를 계산합니다.
    max_frames = int(
        config.max_recording_seconds * config.sample_rate
    )

    # 현재까지 저장된 프레임 수를 0으로 초기화합니다.
    recorded_frames = 0

    def audio_callback(
        input_data: np.ndarray,
        frames: int,
        time_info,
        status: sd.CallbackFlags,
    ) -> None:
        """
        sounddevice가 전달하는 마이크 입력 블록을 큐에 복사합니다.
        """

        # 오디오 입력 상태 경고가 존재하면 콘솔에 출력합니다.
        if status:
            # 오디오 버퍼 오버플로 등의 경고 정보를 출력합니다.
            print(f"\n[오디오 상태 경고] {status}")

        # 다음 콜백에서 버퍼가 변경되지 않도록 현재 오디오 블록을 복사해 큐에 넣습니다.
        audio_queue.put(
            input_data.copy()
        )

    # 녹음 시작 방법을 사용자에게 안내합니다.
    print("\n녹음을 시작합니다.")

    # 녹음을 중지하는 방법을 사용자에게 안내합니다.
    print("말씀을 마친 후 Enter 키를 누르세요.")

    # InputStream 문맥을 열어 마이크 입력 스트림을 시작합니다.
    with sd.InputStream(
        samplerate=config.sample_rate,
        channels=config.channels,
        dtype=config.recording_dtype,
        device=device_index,
        callback=audio_callback,
    ):
        # 사용자가 Enter 키를 누를 때까지 콘솔 입력을 대기합니다.
        input()

        # 큐에 남아 있는 모든 오디오 블록을 순서대로 가져옵니다.
        while not audio_queue.empty():
            # 큐에서 오디오 블록 하나를 꺼냅니다.
            block = audio_queue.get()

            # 가져온 오디오 블록을 리스트에 추가합니다.
            audio_blocks.append(block)

            # 현재 블록의 프레임 수를 누적합니다.
            recorded_frames += block.shape[0]

            # 최대 녹음 프레임을 초과하면 더 이상 블록을 추가하지 않습니다.
            if recorded_frames >= max_frames:
                # 오디오 블록 수집 반복을 종료합니다.
                break

    # 수집된 오디오 블록이 하나도 없는지 검사합니다.
    if not audio_blocks:
        # 실제 녹음 데이터가 없다는 예외를 발생시킵니다.
        raise RuntimeError("녹음된 오디오 데이터가 없습니다.")

    # 여러 오디오 블록을 시간축 방향으로 하나의 배열로 결합합니다.
    audio_data = np.concatenate(
        audio_blocks,
        axis=0,
    )

    # 최대 허용 프레임 수까지만 오디오 데이터를 유지합니다.
    audio_data = audio_data[:max_frames]

    # 중복되지 않는 WAV 파일 저장 경로를 생성합니다.
    output_path = _build_recording_path(config)

    # 결합한 오디오 데이터를 WAV 파일로 저장합니다.
    save_wav(
        file_path=output_path,
        audio_data=audio_data,
        sample_rate=config.sample_rate,
        channels=config.channels,
    )

    # 실제 녹음된 시간을 초 단위로 계산합니다.
    duration = audio_data.shape[0] / config.sample_rate

    # 녹음 시간과 저장 경로를 출력합니다.
    print(f"녹음 완료: {duration:.2f}초, {output_path}")

    # 저장된 WAV 파일 경로를 반환합니다.
    return output_path
