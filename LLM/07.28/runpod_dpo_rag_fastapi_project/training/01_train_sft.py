"""LoRA 기반 SFT를 수행합니다."""
# GPU 정밀도 선택을 위해 torch를 가져옵니다.
import torch
# Hugging Face Dataset을 만들기 위해 Dataset을 가져옵니다.
from datasets import Dataset
# LoRA 설정과 적용 함수를 가져옵니다.
from peft import LoraConfig, get_peft_model
# 모델·토크나이저·Trainer 구성요소를 가져옵니다.
from transformers import AutoModelForCausalLM, AutoTokenizer, DataCollatorForLanguageModeling, Trainer, TrainingArguments
# 공통 유틸리티를 가져옵니다.
from training.common import ROOT, env, read_jsonl, seed_all, show_trainable

# 전체 SFT 파이프라인을 실행합니다.
def main() -> None:
    # 난수 시드를 고정합니다.
    seed_all()
    # 원본 모델 ID를 읽습니다.
    base_id = env('BASE_MODEL', 'Qwen/Qwen2.5-0.5B-Instruct')
    # SFT 어댑터 출력 경로를 계산합니다.
    output = ROOT / env('SFT_ADAPTER', 'outputs/sft_adapter')
    # 출력 폴더를 생성합니다.
    output.mkdir(parents=True, exist_ok=True)
    # 모델 토크나이저를 로드합니다.
    tokenizer = AutoTokenizer.from_pretrained(base_id, trust_remote_code=True, token=env('HF_TOKEN','') or None)
    # 패딩 토큰이 없으면 EOS 토큰을 사용합니다.
    tokenizer.pad_token_id = tokenizer.pad_token_id or tokenizer.eos_token_id
    # 오른쪽 패딩을 사용합니다.
    tokenizer.padding_side = 'right'
    # GPU에서는 float16, CPU에서는 float32를 선택합니다.
    dtype = torch.float16 if torch.cuda.is_available() else torch.float32
    # 원본 causal LM을 로드합니다.
    model = AutoModelForCausalLM.from_pretrained(base_id, torch_dtype=dtype, device_map='auto' if torch.cuda.is_available() else None, trust_remote_code=True, token=env('HF_TOKEN','') or None)
    # 학습 중 KV 캐시를 끕니다.
    model.config.use_cache = False
    # 중간 활성값을 재계산해 GPU 메모리를 절약합니다.
    model.gradient_checkpointing_enable()
    # Qwen 선형 계층에 적용할 LoRA 구성을 정의합니다.
    lora = LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05, bias='none', task_type='CAUSAL_LM', target_modules=['q_proj','k_proj','v_proj','o_proj','gate_proj','up_proj','down_proj'])
    # 원본 모델을 동결하고 LoRA 어댑터를 삽입합니다.
    model = get_peft_model(model, lora)
    # 학습 파라미터 비율을 출력합니다.
    show_trainable(model)
    # JSONL 학습 데이터를 읽습니다.
    dataset = Dataset.from_list(read_jsonl(ROOT / 'data/sft_train.jsonl'))

    # 한 레코드를 채팅 문자열과 토큰으로 변환합니다.
    def tokenize(row):
        # 시스템·사용자·정답 메시지를 구성합니다.
        messages = [{'role':'system','content':'당신은 정확하고 친절한 한국어 AI 조교입니다.'},{'role':'user','content':row['prompt']},{'role':'assistant','content':row['response']}]
        # 모델 고유 채팅 템플릿을 적용합니다.
        text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False)
        # 최대 1024 토큰으로 토큰화합니다.
        return tokenizer(text, truncation=True, max_length=1024, padding=False)

    # 문자열 필드를 제거하고 토큰 데이터셋을 만듭니다.
    tokenized = dataset.map(tokenize, remove_columns=dataset.column_names)
    # causal LM 방식의 배치 collator를 만듭니다.
    collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)
    # SFT 하이퍼파라미터를 정의합니다.
    args = TrainingArguments(output_dir=str(output/'checkpoints'), num_train_epochs=3, per_device_train_batch_size=1, gradient_accumulation_steps=8, learning_rate=2e-4, warmup_ratio=0.05, logging_steps=1, save_strategy='epoch', save_total_limit=2, fp16=torch.cuda.is_available(), report_to='none', remove_unused_columns=False)
    # Trainer 객체를 생성합니다.
    trainer = Trainer(model=model, args=args, train_dataset=tokenized, data_collator=collator)
    # SFT 학습을 수행합니다.
    trainer.train()
    # LoRA 어댑터를 저장합니다.
    model.save_pretrained(output)
    # 토크나이저를 저장합니다.
    tokenizer.save_pretrained(output)
    # 완료 경로를 출력합니다.
    print(f'SFT 저장 완료: {output}')

# 직접 실행할 때만 main을 호출합니다.
if __name__ == '__main__':
    # SFT를 시작합니다.
    main()
