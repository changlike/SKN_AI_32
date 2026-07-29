"""
마이크 음성을 녹음하고 텍스트로 변환하는 콘솔 프로그램의 시작 파일입니다.

메뉴 기능
1. 오디오 입력 장치 목록 확인
2. 지정 시간 동안 녹음 후 텍스트 변환
3. Enter 키를 누를 때까지 녹음 후 텍스트 변환
4. 기존 WAV 파일 텍스트 변환
5. 설정 정보 확인
0. 프로그램 종료
"""

# 프로그램의 비정상 종료 코드를 운영체제에 전달하기 위해 sys 모듈을 가져옵니다.
import sys

# 프로젝트 환경 설정을 관리하는 Config 클래스를 가져옵니다.
from src.config import Config

# 마이크 장치 목록과 녹음 기능을 제공하는 함수를 가져옵니다.
from src.audio_recorder import (
    list_input_devices,
    record_for_seconds,
    record_until_enter,
)

# WAV 음성을 텍스트로 변환하는 SpeechToTextService 클래스를 가져옵니다.
from src.transcriber import SpeechToTextService

# 변환 결과를 텍스트와 JSON 파일로 저장하는 함수를 가져옵니다.
from src.result_writer import save_transcription_result


def print_title() -> None:
    """
    프로그램 제목과 핵심 처리 흐름을 콘솔에 출력합니다.
    """

    # 제목 위쪽의 구분선을 출력합니다.
    print("\n" + "=" * 80)

    # 프로젝트의 이름을 출력합니다.
    print(" 마이크 음성 → 텍스트 변환 PyCharm 콘솔 프로젝트")

    # 제목 아래쪽의 구분선을 출력합니다.
    print("=" * 80)

    # 사용자가 이해할 수 있도록 전체 처리 흐름을 출력합니다.
    print("마이크 입력 → WAV 녹음 → Faster-Whisper 음성 인식 → TXT/JSON 저장")


def print_menu() -> None:
    """
    사용자가 선택할 수 있는 메인 메뉴를 출력합니다.
    """

    # 메뉴 시작 구분선을 출력합니다.
    print("\n" + "-" * 80)

    # 첫 번째 메뉴를 출력합니다.
    print("1. 오디오 입력 장치 목록 확인")

    # 두 번째 메뉴를 출력합니다.
    print("2. 지정 시간 동안 녹음 후 텍스트 변환")

    # 세 번째 메뉴를 출력합니다.
    print("3. Enter 키를 누를 때까지 녹음 후 텍스트 변환")

    # 네 번째 메뉴를 출력합니다.
    print("4. 기존 WAV 파일 텍스트 변환")

    # 다섯 번째 메뉴를 출력합니다.
    print("5. 현재 설정 정보 확인")

    # 종료 메뉴를 출력합니다.
    print("0. 프로그램 종료")

    # 메뉴 종료 구분선을 출력합니다.
    print("-" * 80)


def pause() -> None:
    """
    사용자가 실행 결과를 확인한 후 메인 메뉴로 돌아가도록 대기합니다.
    """

    # 사용자가 Enter 키를 누를 때까지 프로그램 실행을 잠시 멈춥니다.
    input("\nEnter 키를 누르면 메인 메뉴로 돌아갑니다.")


def ask_device_index() -> int | None:
    """
    사용할 입력 장치 번호를 사용자에게 입력받습니다.

    Returns:
        장치 번호를 입력하지 않으면 None을 반환하고,
        숫자를 입력하면 해당 정수 장치 번호를 반환합니다.
    """

    # 기본 입력 장치를 사용할 수 있도록 장치 번호 입력을 안내합니다.
    raw_value = input(
        "사용할 입력 장치 번호를 입력하세요."
        " 기본 장치는 Enter를 누르세요: "
    ).strip()

    # 사용자가 아무 값도 입력하지 않은 경우 기본 장치를 의미하는 None을 반환합니다.
    if raw_value == "":
        # sounddevice가 운영체제의 기본 입력 장치를 사용하도록 None을 반환합니다.
        return None

    # 입력된 문자열을 정수 장치 번호로 변환합니다.
    return int(raw_value)


def transcribe_and_save(
    config: Config,
    service: SpeechToTextService,
    audio_path,
) -> None:
    """
    WAV 파일을 텍스트로 변환하고 결과 파일을 저장합니다.
    """

    # 음성 인식을 시작한다는 안내 메시지를 출력합니다.
    print("\n음성을 텍스트로 변환하고 있습니다.")

    # 저장된 WAV 파일을 음성 인식 서비스에 전달합니다.
    result = service.transcribe(
        audio_path=audio_path,
    )

    # 인식된 언어와 확률을 출력합니다.
    print(
        f"\n감지 언어: {result.language} "
        f"(확률: {result.language_probability:.4f})"
    )

    # 전체 변환 문장을 출력합니다.
    print("\n[전체 변환 텍스트]")

    # 음성에서 인식된 전체 텍스트를 출력합니다.
    print(result.text if result.text else "(인식된 텍스트가 없습니다.)")

    # 구간별 시작 시간, 종료 시간 및 문장을 출력합니다.
    print("\n[구간별 변환 결과]")

    # 인식 결과의 모든 음성 구간을 순서대로 반복합니다.
    for segment in result.segments:
        # 각 구간의 시간 정보와 문장을 출력합니다.
        print(
            f"[{segment.start:8.2f}초 ~ {segment.end:8.2f}초] "
            f"{segment.text}"
        )

    # 전체 결과를 TXT와 JSON 파일로 저장합니다.
    saved_paths = save_transcription_result(
        config=config,
        result=result,
        source_audio_path=audio_path,
    )

    # 저장된 TXT 파일 경로를 출력합니다.
    print(f"\nTXT 저장 경로: {saved_paths['text']}")

    # 저장된 JSON 파일 경로를 출력합니다.
    print(f"JSON 저장 경로: {saved_paths['json']}")


def show_config(config: Config) -> None:
    """
    현재 프로젝트의 녹음 및 음성 인식 설정값을 출력합니다.
    """

    # 설정 정보 제목을 출력합니다.
    print("\n[현재 설정 정보]")

    # 오디오 샘플링 주파수를 출력합니다.
    print(f"샘플링 주파수: {config.sample_rate} Hz")

    # 오디오 채널 수를 출력합니다.
    print(f"채널 수: {config.channels}")

    # 기본 고정 녹음 시간을 출력합니다.
    print(f"기본 녹음 시간: {config.default_duration_seconds}초")

    # Faster-Whisper 모델 크기를 출력합니다.
    print(f"Whisper 모델: {config.model_size}")

    # 모델 실행 장치를 출력합니다.
    print(f"모델 실행 장치: {config.device}")

    # 모델 계산 자료형을 출력합니다.
    print(f"계산 자료형: {config.compute_type}")

    # 음성 인식 언어 설정을 출력합니다.
    print(f"언어 설정: {config.language or '자동 감지'}")

    # 음성 활동 감지 필터 사용 여부를 출력합니다.
    print(f"VAD 필터: {config.vad_filter}")

    # 녹음 파일 저장 폴더를 출력합니다.
    print(f"녹음 저장 폴더: {config.recordings_dir}")

    # 변환 결과 저장 폴더를 출력합니다.
    print(f"결과 저장 폴더: {config.results_dir}")


def main() -> None:
    """
    콘솔 메뉴를 반복 실행하는 프로그램의 메인 함수입니다.
    """

    # 프로젝트 설정 객체를 생성합니다.
    config = Config()

    # 프로그램 제목을 출력합니다.
    print_title()

    # 음성 인식 모델을 필요한 시점에 한 번만 생성하기 위해 초기값을 None으로 설정합니다.
    service = None

    # 사용자가 종료 메뉴를 선택할 때까지 메뉴를 반복합니다.
    while True:
        # 사용 가능한 메뉴를 출력합니다.
        print_menu()

        # 사용자가 선택한 메뉴 번호를 문자열로 입력받습니다.
        choice = input("실행할 메뉴 번호를 입력하세요: ").strip()

        # 사용자가 1번을 선택하면 입력 장치 목록을 출력합니다.
        if choice == "1":
            # 현재 컴퓨터에서 사용할 수 있는 마이크 장치 목록을 출력합니다.
            list_input_devices()

            # 사용자가 결과를 확인할 수 있도록 대기합니다.
            pause()

        # 사용자가 2번을 선택하면 지정 시간 녹음을 수행합니다.
        elif choice == "2":
            # 녹음 시간을 문자열로 입력받습니다.
            duration_text = input(
                f"녹음 시간을 초 단위로 입력하세요 "
                f"(기본 {config.default_duration_seconds}초): "
            ).strip()

            # 사용자가 시간을 입력하지 않으면 기본 녹음 시간을 사용합니다.
            duration = (
                config.default_duration_seconds
                if duration_text == ""
                else float(duration_text)
            )

            # 사용할 마이크 장치 번호를 입력받습니다.
            device_index = ask_device_index()

            # 지정한 시간 동안 마이크 음성을 녹음하고 WAV 파일을 저장합니다.
            audio_path = record_for_seconds(
                config=config,
                duration_seconds=duration,
                device_index=device_index,
            )

            # 음성 인식 서비스가 아직 생성되지 않았다면 모델을 로드합니다.
            if service is None:
                # Faster-Whisper 기반 음성 인식 서비스 객체를 생성합니다.
                service = SpeechToTextService(config)

            # 녹음된 음성을 텍스트로 변환하고 결과를 저장합니다.
            transcribe_and_save(
                config=config,
                service=service,
                audio_path=audio_path,
            )

            # 결과를 확인할 수 있도록 대기합니다.
            pause()

        # 사용자가 3번을 선택하면 Enter 종료 방식의 녹음을 수행합니다.
        elif choice == "3":
            # 사용할 마이크 장치 번호를 입력받습니다.
            device_index = ask_device_index()

            # 사용자가 Enter 키를 누를 때까지 마이크 입력을 녹음합니다.
            audio_path = record_until_enter(
                config=config,
                device_index=device_index,
            )

            # 음성 인식 서비스가 아직 생성되지 않았다면 모델을 로드합니다.
            if service is None:
                # Faster-Whisper 기반 음성 인식 서비스 객체를 생성합니다.
                service = SpeechToTextService(config)

            # 녹음된 WAV 파일을 텍스트로 변환하고 결과를 저장합니다.
            transcribe_and_save(
                config=config,
                service=service,
                audio_path=audio_path,
            )

            # 결과를 확인할 수 있도록 대기합니다.
            pause()

        # 사용자가 4번을 선택하면 기존 WAV 파일을 변환합니다.
        elif choice == "4":
            # 변환할 WAV 파일 경로를 입력받습니다.
            audio_path = input("변환할 WAV 파일 경로를 입력하세요: ").strip()

            # 음성 인식 서비스가 아직 생성되지 않았다면 모델을 로드합니다.
            if service is None:
                # Faster-Whisper 기반 음성 인식 서비스 객체를 생성합니다.
                service = SpeechToTextService(config)

            # 지정한 WAV 파일을 텍스트로 변환하고 결과를 저장합니다.
            transcribe_and_save(
                config=config,
                service=service,
                audio_path=audio_path,
            )

            # 결과를 확인할 수 있도록 대기합니다.
            pause()

        # 사용자가 5번을 선택하면 현재 설정 정보를 출력합니다.
        elif choice == "5":
            # 프로젝트의 현재 녹음 및 모델 설정을 출력합니다.
            show_config(config)

            # 결과를 확인할 수 있도록 대기합니다.
            pause()

        # 사용자가 0번을 선택하면 프로그램을 종료합니다.
        elif choice == "0":
            # 프로그램 종료 메시지를 출력합니다.
            print("\n프로그램을 종료합니다.")

            # 메뉴 반복문을 종료합니다.
            break

        # 정의되지 않은 메뉴 번호가 입력된 경우 오류 메시지를 출력합니다.
        else:
            # 올바른 범위의 메뉴 번호를 다시 입력하도록 안내합니다.
            print("\n[입력 오류] 0부터 5 사이의 번호를 입력하세요.")


# 현재 파일이 다른 모듈에서 import된 것이 아니라 직접 실행된 경우에만 실행합니다.
if __name__ == "__main__":
    try:
        # 프로그램의 메인 함수를 호출합니다.
        main()

    except KeyboardInterrupt:
        # 사용자가 Ctrl+C를 누른 경우 줄을 바꾸고 종료 메시지를 출력합니다.
        print("\n\n사용자 요청으로 프로그램을 종료합니다.")

        # 운영체제에 정상 종료 상태 코드 0을 반환합니다.
        sys.exit(0)

    except ValueError as error:
        # 숫자 변환이나 설정값 오류를 사용자에게 출력합니다.
        print(f"\n[입력 또는 설정 오류] {error}")

        # 운영체제에 비정상 종료 상태 코드 1을 반환합니다.
        sys.exit(1)

    except Exception as error:
        # 그 밖의 처리되지 않은 오류 종류와 메시지를 출력합니다.
        print(f"\n[실행 오류] {type(error).__name__}: {error}")

        # 운영체제에 비정상 종료 상태 코드 1을 반환합니다.
        sys.exit(1)
