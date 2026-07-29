"""CNN 실제 이미지 분류 프로젝트의 콘솔 메뉴를 실행하는 파일입니다."""

# 프로그램을 안전하게 종료하기 위해 sys 모듈을 가져옵니다.
import sys

# 프로젝트 전체 설정을 관리하는 Config 클래스를 가져옵니다.
from src.config import Config

# 데이터셋 점검, 데이터 분리, 증강 샘플 저장 기능을 가져옵니다.
from src.data import inspect_dataset, prepare_dataloaders, save_augmentation_preview

# 신규 학습, 재개 학습, 테스트 평가 기능을 가져옵니다.
from src.trainer import train_new_model, resume_training, evaluate_best_model

# 저장된 모델을 이용한 단일 이미지 예측 기능을 가져옵니다.
from src.predict import predict_image

# 난수 시드 고정과 실행 환경 출력 기능을 가져옵니다.
from src.utils import set_seed, print_environment


def print_header() -> None:
    """프로젝트 제목을 출력합니다."""

    # 제목 위쪽 구분선을 출력합니다.
    print("\n" + "=" * 80)

    # 프로젝트 이름을 출력합니다.
    print(" CNN 실제 이미지 분류 PyCharm 콘솔 프로젝트")

    # 제목 아래쪽 구분선을 출력합니다.
    print("=" * 80)

    # 구현된 주요 기능을 요약하여 출력합니다.
    print("데이터 분리 · 검증 · 테스트 · 증강 · 모델 저장 · 체크포인트 · 조기 종료")


def print_menu() -> None:
    """사용 가능한 메뉴를 출력합니다."""

    # 메뉴 구분선을 출력합니다.
    print("\n" + "-" * 80)

    # 데이터셋 확인 메뉴를 출력합니다.
    print("1. 데이터셋 구조와 클래스 정보 확인")

    # 데이터 분할 확인 메뉴를 출력합니다.
    print("2. 학습/검증/테스트 분할 결과 확인")

    # 데이터 증강 확인 메뉴를 출력합니다.
    print("3. 데이터 증강 미리보기 저장")

    # 신규 학습 메뉴를 출력합니다.
    print("4. CNN 신규 학습")

    # 테스트 평가 메뉴를 출력합니다.
    print("5. 저장된 최적 모델 테스트 평가")

    # 단일 이미지 예측 메뉴를 출력합니다.
    print("6. 단일 이미지 분류")

    # 체크포인트 학습 재개 메뉴를 출력합니다.
    print("7. 체크포인트에서 학습 재개")

    # 실행 환경 확인 메뉴를 출력합니다.
    print("8. 실행 환경 확인")

    # 프로그램 종료 메뉴를 출력합니다.
    print("0. 프로그램 종료")

    # 메뉴 구분선을 출력합니다.
    print("-" * 80)


def pause() -> None:
    """사용자가 결과를 확인할 수 있도록 Enter 입력을 기다립니다."""

    # 사용자가 Enter 키를 누를 때까지 프로그램을 잠시 멈춥니다.
    input("\nEnter 키를 누르면 메인 메뉴로 돌아갑니다.")


def main() -> None:
    """콘솔 메뉴의 전체 실행 흐름을 관리합니다."""

    # 프로젝트 설정 객체를 생성합니다.
    config = Config()

    # 데이터 분할과 학습 결과를 재현할 수 있도록 난수 시드를 고정합니다.
    set_seed(config.seed)

    # 프로그램 제목을 출력합니다.
    print_header()

    # 사용자가 종료 메뉴를 선택할 때까지 반복합니다.
    while True:
        # 메뉴 목록을 출력합니다.
        print_menu()

        # 사용자가 입력한 메뉴 번호를 읽고 양쪽 공백을 제거합니다.
        choice = input("실행할 메뉴 번호를 입력하세요: ").strip()

        # 1번 메뉴가 선택되면 데이터셋 구조를 점검합니다.
        if choice == "1":
            # 클래스 폴더와 이미지 수를 출력합니다.
            inspect_dataset(config)
            # 결과 확인을 위해 입력을 기다립니다.
            pause()

        # 2번 메뉴가 선택되면 데이터 분할 결과를 확인합니다.
        elif choice == "2":
            # 데이터셋과 DataLoader를 준비합니다.
            bundle = prepare_dataloaders(config)
            # 학습 데이터 수를 출력합니다.
            print(f"\n학습 데이터: {len(bundle.train_dataset)}개")
            # 검증 데이터 수를 출력합니다.
            print(f"검증 데이터: {len(bundle.val_dataset)}개")
            # 테스트 데이터 수를 출력합니다.
            print(f"테스트 데이터: {len(bundle.test_dataset)}개")
            # 클래스 이름 목록을 출력합니다.
            print(f"클래스 목록: {bundle.class_names}")
            # 결과 확인을 위해 입력을 기다립니다.
            pause()

        # 3번 메뉴가 선택되면 증강 이미지를 저장합니다.
        elif choice == "3":
            # 동일한 이미지에 다양한 증강을 적용한 미리보기를 저장합니다.
            save_augmentation_preview(config)
            # 결과 확인을 위해 입력을 기다립니다.
            pause()

        # 4번 메뉴가 선택되면 처음부터 모델을 학습합니다.
        elif choice == "4":
            # 새 CNN 모델의 학습을 실행합니다.
            train_new_model(config)
            # 결과 확인을 위해 입력을 기다립니다.
            pause()

        # 5번 메뉴가 선택되면 최적 모델을 테스트합니다.
        elif choice == "5":
            # 저장된 최적 모델로 테스트 데이터의 성능을 평가합니다.
            evaluate_best_model(config)
            # 결과 확인을 위해 입력을 기다립니다.
            pause()

        # 6번 메뉴가 선택되면 하나의 이미지 파일을 분류합니다.
        elif choice == "6":
            # 분류할 이미지 경로를 사용자에게 입력받습니다.
            image_path = input("분류할 이미지 경로를 입력하세요: ").strip()
            # 입력한 이미지를 저장 모델로 분류합니다.
            predict_image(config, image_path)
            # 결과 확인을 위해 입력을 기다립니다.
            pause()

        # 7번 메뉴가 선택되면 마지막 체크포인트부터 학습을 재개합니다.
        elif choice == "7":
            # 모델, 옵티마이저, 스케줄러 상태를 복원하여 추가 학습합니다.
            resume_training(config)
            # 결과 확인을 위해 입력을 기다립니다.
            pause()

        # 8번 메뉴가 선택되면 현재 실행 환경을 출력합니다.
        elif choice == "8":
            # Python, PyTorch, CUDA 정보를 출력합니다.
            print_environment()
            # 결과 확인을 위해 입력을 기다립니다.
            pause()

        # 0번 메뉴가 선택되면 프로그램을 종료합니다.
        elif choice == "0":
            # 종료 메시지를 출력합니다.
            print("\n프로그램을 종료합니다.")
            # while 반복문을 종료합니다.
            break

        # 정의되지 않은 값이 입력되면 오류 메시지를 출력합니다.
        else:
            # 올바른 메뉴 번호를 입력하도록 안내합니다.
            print("\n[입력 오류] 0부터 8 사이의 번호를 입력하세요.")


# 현재 파일이 직접 실행된 경우에만 프로그램을 시작합니다.
if __name__ == "__main__":
    try:
        # 메인 함수를 호출합니다.
        main()
    except KeyboardInterrupt:
        # 사용자가 Ctrl+C를 누르면 종료 메시지를 출력합니다.
        print("\n\n사용자 요청으로 프로그램을 종료합니다.")
        # 정상 종료 상태 코드를 반환합니다.
        sys.exit(0)
    except Exception as error:
        # 처리되지 않은 오류의 종류와 메시지를 출력합니다.
        print(f"\n[실행 오류] {type(error).__name__}: {error}")
        # 비정상 종료 상태 코드를 반환합니다.
        sys.exit(1)
