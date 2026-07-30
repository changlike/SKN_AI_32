"""프로젝트에 포함된 RAG 근거 문서를 확인하는 실행 스크립트입니다."""
from pathlib import Path

DOCS_DIR = Path(__file__).resolve().parent / "data" / "docs"
REQUIRED = {
    "membership_policy.pdf": 6243,
    "product_manual_robot_vacuum.pdf": 7495,
    "product_manual_smartwatch.pdf": 5955,
    "employee_handbook.pdf": 7651,
    "refund_exchange_policy.pdf": 9293,
}

print(f"문서 폴더: {DOCS_DIR}")
missing = []
for name, minimum_size in REQUIRED.items():
    path = DOCS_DIR / name
    if not path.exists():
        missing.append(name)
        print(f"[누락] {name}")
        continue
    size = path.stat().st_size
    status = "정상" if size >= minimum_size else "크기 이상"
    print(f"[{status}] {name}: {size:,} bytes")

if missing:
    raise SystemExit(f"필수 문서 {len(missing)}개가 누락되었습니다.")
print("RAG 근거 문서 5개가 모두 정상적으로 포함되어 있습니다.")
