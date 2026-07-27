"""
RunPod 환경에서 PyTorch와 CUDA GPU 상태를 확인합니다.
"""

# GPU 확인을 위해 PyTorch를 가져옵니다.
import torch


def main() -> None:
    """
    PyTorch 버전, CUDA, GPU, BF16 지원 여부를 출력합니다.
    """

    # 설치된 PyTorch 버전을 출력합니다.
    print("torch version:", torch.__version__)

    # PyTorch 빌드에 연결된 CUDA 버전을 출력합니다.
    print("torch CUDA version:", torch.version.cuda)

    # CUDA GPU 사용 가능 여부를 출력합니다.
    print("CUDA available:", torch.cuda.is_available())

    # GPU가 없으면 이후 GPU 정보 조회를 중단합니다.
    if not torch.cuda.is_available():
        return

    # 현재 사용 가능한 GPU 개수를 출력합니다.
    print("GPU count:", torch.cuda.device_count())

    # 각 GPU 정보를 반복해서 출력합니다.
    for index in range(torch.cuda.device_count()):
        # 현재 GPU의 속성을 읽습니다.
        properties = torch.cuda.get_device_properties(index)

        # GPU 이름을 출력합니다.
        print(f"GPU {index} name:", properties.name)

        # GPU 전체 메모리를 GiB 단위로 출력합니다.
        print(
            f"GPU {index} memory GiB:",
            round(properties.total_memory / (1024 ** 3), 2),
        )

    # 현재 GPU의 BF16 지원 여부를 출력합니다.
    print("BF16 supported:", torch.cuda.is_bf16_supported())


# 직접 실행한 경우에만 GPU 정보를 출력합니다.
if __name__ == "__main__":
    main()
