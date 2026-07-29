"""
CNN 구조와 연산 원리를 콘솔에서 단계별로 확인하는 메인 실행 파일입니다.

이 프로그램은 다음 내용을 메뉴 방식으로 실행합니다.

1. CNN 전체 구조 확인
2. NumPy 기반 2차원 합성곱 연산
3. 스트라이드와 패딩에 따른 출력 크기 비교
4. ReLU 활성화 함수 연산
5. 최대 풀링과 평균 풀링 연산
6. 다중 채널 합성곱 연산
7. PyTorch CNN 순전파와 텐서 크기 확인
8. 합성곱 계층의 파라미터 수 계산
9. 간단한 CNN 학습과 역전파 확인
0. 프로그램 종료
"""

# 표준 라이브러리의 sys 모듈을 가져옵니다.
# sys 모듈은 파이썬 실행 환경과 관련된 기능을 제공합니다.
import sys

# 각 실습 기능을 구현한 demos 패키지의 함수들을 가져옵니다.
from demos.cnn_structure_demo import run_cnn_structure_demo
from demos.convolution_demo import run_convolution_demo
from demos.output_size_demo import run_output_size_demo
from demos.activation_demo import run_activation_demo
from demos.pooling_demo import run_pooling_demo
from demos.multichannel_demo import run_multichannel_demo
from demos.pytorch_forward_demo import run_pytorch_forward_demo
from demos.parameter_demo import run_parameter_demo
from demos.training_demo import run_training_demo


def print_title() -> None:
    """
    프로그램의 제목과 설명을 콘솔에 출력합니다.
    """

    # 프로그램 제목의 위쪽 구분선을 출력합니다.
    print("\n" + "=" * 72)

    # 프로그램의 이름을 출력합니다.
    print(" CNN 구조와 연산 원리 학습용 PyCharm 콘솔 프로젝트")

    # 프로그램 제목의 아래쪽 구분선을 출력합니다.
    print("=" * 72)

    # 프로그램에서 학습할 수 있는 핵심 내용을 출력합니다.
    print("합성곱, 패딩, 스트라이드, ReLU, 풀링, 다중 채널, 순전파, 역전파")


def print_menu() -> None:
    """
    사용자가 선택할 수 있는 메인 메뉴를 출력합니다.
    """

    # 메뉴의 시작을 알리는 구분선을 출력합니다.
    print("\n" + "-" * 72)

    # 첫 번째 메뉴 항목을 출력합니다.
    print("1. CNN 전체 구조 확인")

    # 두 번째 메뉴 항목을 출력합니다.
    print("2. NumPy 기반 2차원 합성곱 연산")

    # 세 번째 메뉴 항목을 출력합니다.
    print("3. 스트라이드와 패딩에 따른 출력 크기 비교")

    # 네 번째 메뉴 항목을 출력합니다.
    print("4. ReLU 활성화 함수 연산")

    # 다섯 번째 메뉴 항목을 출력합니다.
    print("5. 최대 풀링과 평균 풀링 연산")

    # 여섯 번째 메뉴 항목을 출력합니다.
    print("6. 다중 채널 합성곱 연산")

    # 일곱 번째 메뉴 항목을 출력합니다.
    print("7. PyTorch CNN 순전파와 텐서 크기 확인")

    # 여덟 번째 메뉴 항목을 출력합니다.
    print("8. 합성곱 계층의 파라미터 수 계산")

    # 아홉 번째 메뉴 항목을 출력합니다.
    print("9. 간단한 CNN 학습과 역전파 확인")

    # 프로그램 종료 메뉴를 출력합니다.
    print("0. 프로그램 종료")

    # 메뉴의 끝을 알리는 구분선을 출력합니다.
    print("-" * 72)


def pause() -> None:
    """
    사용자가 실행 결과를 충분히 확인한 후 메뉴로 돌아갈 수 있도록 대기합니다.
    """

    # 사용자가 Enter 키를 입력할 때까지 프로그램 실행을 잠시 멈춥니다.
    input("\nEnter 키를 누르면 메인 메뉴로 돌아갑니다.")


def main() -> None:
    """
    프로그램의 전체 실행 흐름을 관리하는 메인 함수입니다.
    """

    # 프로그램 시작 시 제목을 한 번 출력합니다.
    print_title()

    # 사용자가 종료 메뉴를 선택할 때까지 메뉴를 반복해서 표시합니다.
    while True:
        # 현재 사용 가능한 메뉴를 출력합니다.
        print_menu()

        # 사용자가 입력한 메뉴 번호를 문자열 형태로 전달받습니다.
        choice = input("실행할 메뉴 번호를 입력하세요: ").strip()

        # 사용자가 1번을 선택한 경우 CNN 전체 구조 설명을 실행합니다.
        if choice == "1":
            # CNN 전체 구조 실습 함수를 호출합니다.
            run_cnn_structure_demo()

            # 실행 결과를 확인할 수 있도록 잠시 대기합니다.
            pause()

        # 사용자가 2번을 선택한 경우 2차원 합성곱 실습을 실행합니다.
        elif choice == "2":
            # NumPy 기반 합성곱 연산 실습 함수를 호출합니다.
            run_convolution_demo()

            # 실행 결과를 확인할 수 있도록 잠시 대기합니다.
            pause()

        # 사용자가 3번을 선택한 경우 출력 크기 비교 실습을 실행합니다.
        elif choice == "3":
            # 스트라이드와 패딩에 따른 출력 크기 비교 함수를 호출합니다.
            run_output_size_demo()

            # 실행 결과를 확인할 수 있도록 잠시 대기합니다.
            pause()

        # 사용자가 4번을 선택한 경우 ReLU 실습을 실행합니다.
        elif choice == "4":
            # ReLU 활성화 함수 실습 함수를 호출합니다.
            run_activation_demo()

            # 실행 결과를 확인할 수 있도록 잠시 대기합니다.
            pause()

        # 사용자가 5번을 선택한 경우 풀링 실습을 실행합니다.
        elif choice == "5":
            # 최대 풀링과 평균 풀링 실습 함수를 호출합니다.
            run_pooling_demo()

            # 실행 결과를 확인할 수 있도록 잠시 대기합니다.
            pause()

        # 사용자가 6번을 선택한 경우 다중 채널 합성곱 실습을 실행합니다.
        elif choice == "6":
            # RGB 형태의 다중 채널 합성곱 실습 함수를 호출합니다.
            run_multichannel_demo()

            # 실행 결과를 확인할 수 있도록 잠시 대기합니다.
            pause()

        # 사용자가 7번을 선택한 경우 PyTorch 순전파 실습을 실행합니다.
        elif choice == "7":
            # CNN 계층별 텐서 크기 실습 함수를 호출합니다.
            run_pytorch_forward_demo()

            # 실행 결과를 확인할 수 있도록 잠시 대기합니다.
            pause()

        # 사용자가 8번을 선택한 경우 파라미터 계산 실습을 실행합니다.
        elif choice == "8":
            # 합성곱 계층의 파라미터 수 계산 함수를 호출합니다.
            run_parameter_demo()

            # 실행 결과를 확인할 수 있도록 잠시 대기합니다.
            pause()

        # 사용자가 9번을 선택한 경우 CNN 학습 실습을 실행합니다.
        elif choice == "9":
            # 합성 데이터 기반 CNN 학습과 역전파 실습 함수를 호출합니다.
            run_training_demo()

            # 실행 결과를 확인할 수 있도록 잠시 대기합니다.
            pause()

        # 사용자가 0번을 선택한 경우 프로그램을 종료합니다.
        elif choice == "0":
            # 종료 메시지를 출력합니다.
            print("\n프로그램을 종료합니다.")

            # while 반복문을 종료합니다.
            break

        # 정의되지 않은 메뉴 번호가 입력된 경우 오류 메시지를 출력합니다.
        else:
            # 올바른 메뉴 번호를 다시 입력하도록 안내합니다.
            print("\n[입력 오류] 0부터 9 사이의 메뉴 번호를 입력하세요.")


# 현재 파일이 직접 실행된 경우에만 아래 코드를 실행합니다.
if __name__ == "__main__":
    try:
        # 프로그램의 메인 함수를 호출합니다.
        main()

    except KeyboardInterrupt:
        # 사용자가 Ctrl+C를 입력한 경우 줄을 바꾸고 종료 메시지를 출력합니다.
        print("\n\n사용자 요청으로 프로그램을 종료합니다.")

        # 운영체제에 정상 종료 코드 0을 반환합니다.
        sys.exit(0)

    except Exception as error:
        # 처리되지 않은 오류의 클래스 이름과 메시지를 출력합니다.
        print(f"\n[실행 오류] {type(error).__name__}: {error}")

        # 운영체제에 비정상 종료 코드 1을 반환합니다.
        sys.exit(1)
