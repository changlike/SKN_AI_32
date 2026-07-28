"""DPO LoRA 어댑터를 원본 모델에 병합합니다."""
# GPU 정밀도 선택을 위해 torch를 가져옵니다.
import torch
# PEFT 어댑터 연결을 위해 PeftModel을 가져옵니다.
from peft import PeftModel
# 모델과 토크나이저를 가져옵니다.
from transformers import AutoModelForCausalLM, AutoTokenizer
# 공통 설정을 가져옵니다.
from training.common import ROOT, env

# 병합 과정을 실행합니다.
def main() -> None:
    # 원본 모델 ID를 읽습니다.
    base_id = env('BASE_MODEL','Qwen/Qwen2.5-0.5B-Instruct')
    # DPO 어댑터 경로를 계산합니다.
    adapter = ROOT / env('DPO_ADAPTER','outputs/dpo_adapter')
    # 병합 모델 출력 경로를 계산합니다.
    output = ROOT / env('MERGED_MODEL','outputs/dpo_merged')
    # 출력 폴더를 생성합니다.
    output.mkdir(parents=True, exist_ok=True)
    # GPU에서는 float16을 선택합니다.
    dtype = torch.float16 if torch.cuda.is_available() else torch.float32
    # 원본 모델을 로드합니다.
    base = AutoModelForCausalLM.from_pretrained(base_id, torch_dtype=dtype, device_map='auto' if torch.cuda.is_available() else None, trust_remote_code=True, token=env('HF_TOKEN','') or None)
    # DPO 어댑터를 원본 모델에 연결합니다.
    peft_model = PeftModel.from_pretrained(base, adapter)
    # LoRA 가중치를 원본 가중치에 합치고 어댑터 구조를 제거합니다.
    merged = peft_model.merge_and_unload()
    # 일반 Hugging Face 모델 형식으로 저장합니다.
    merged.save_pretrained(output, safe_serialization=True)
    # DPO 토크나이저를 로드합니다.
    tokenizer = AutoTokenizer.from_pretrained(adapter, trust_remote_code=True)
    # 병합 모델 경로에 토크나이저를 저장합니다.
    tokenizer.save_pretrained(output)
    # 완료 경로를 출력합니다.
    print(f'병합 완료: {output}')

# 직접 실행할 때만 main을 호출합니다.
if __name__ == '__main__':
    # 모델 병합을 시작합니다.
    main()
