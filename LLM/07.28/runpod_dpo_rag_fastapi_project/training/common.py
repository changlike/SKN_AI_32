"""학습·평가 공통 함수입니다."""
# JSONL 파일을 읽기 위해 json을 가져옵니다.
import json
# 환경변수를 읽기 위해 os를 가져옵니다.
import os
# 경로 처리를 위해 Path를 가져옵니다.
from pathlib import Path
# 다양한 JSON 값 타입을 위해 Any를 가져옵니다.
from typing import Any
# 난수 시드와 GPU 판별을 위해 torch를 가져옵니다.
import torch
# .env 파일을 현재 프로세스에 로드합니다.
from dotenv import load_dotenv

# 현재 파일 기준 프로젝트 루트 경로입니다.
ROOT = Path(__file__).resolve().parents[1]
# 프로젝트 루트의 .env 파일을 읽습니다.
load_dotenv(ROOT / '.env')

# 환경변수가 없을 때 기본값을 반환합니다.
def env(name: str, default: str) -> str:
    # 시스템 환경변수 또는 기본값을 반환합니다.
    return os.getenv(name, default)

# 실험 재현성을 위해 난수 시드를 고정합니다.
def seed_all(seed: int = 42) -> None:
    # CPU 난수 시드를 고정합니다.
    torch.manual_seed(seed)
    # CUDA가 있으면 모든 GPU 난수 시드도 고정합니다.
    if torch.cuda.is_available():
        # 다중 GPU 전체에 같은 시드를 적용합니다.
        torch.cuda.manual_seed_all(seed)

# 한 줄에 하나의 JSON 객체가 있는 JSONL 파일을 읽습니다.
def read_jsonl(path: Path) -> list[dict[str, Any]]:
    # 결과 레코드를 저장할 목록입니다.
    rows: list[dict[str, Any]] = []
    # UTF-8 텍스트 파일을 엽니다.
    with path.open('r', encoding='utf-8') as file:
        # 파일을 줄 단위로 순회합니다.
        for number, line in enumerate(file, 1):
            # 앞뒤 공백을 제거합니다.
            line = line.strip()
            # 빈 줄은 건너뜁니다.
            if not line:
                # 다음 줄로 이동합니다.
                continue
            try:
                # JSON 문자열을 딕셔너리로 변환합니다.
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                # 파일과 줄 번호가 포함된 오류로 변환합니다.
                raise ValueError(f'{path}:{number} JSON 오류') from exc
    # 읽은 레코드를 반환합니다.
    return rows

# 모델의 실제 학습 대상 파라미터 비율을 출력합니다.
def show_trainable(model: Any) -> None:
    # 전체 파라미터 수를 계산합니다.
    total = sum(p.numel() for p in model.parameters())
    # gradient를 계산하는 파라미터 수를 계산합니다.
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    # 개수와 비율을 출력합니다.
    print(f'trainable={trainable:,} / total={total:,} ({100*trainable/max(total,1):.4f}%)')
