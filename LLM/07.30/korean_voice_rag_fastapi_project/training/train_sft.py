"""Qwen 계열 모델을 한국어 상담 데이터로 LoRA 파인튜닝합니다."""
from pathlib import Path  # 학습 데이터와 출력 경로를 처리합니다.
import torch  # GPU와 자료형을 제어합니다.
from datasets import load_dataset  # JSONL 학습 데이터를 읽습니다.
from peft import LoraConfig, TaskType  # LoRA 어댑터 설정을 정의합니다.
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments  # 모델, 토크나이저, 학습 옵션을 가져옵니다.
from trl import SFTTrainer  # 지도 파인튜닝 트레이너를 가져옵니다.
BASE=Path(__file__).resolve().parent.parent  # 프로젝트 루트를 계산합니다.
MODEL='Qwen/Qwen2.5-1.5B-Instruct'  # 원본 모델 이름입니다.
OUT=BASE/'models/finetuned_model'  # LoRA 어댑터 저장 경로입니다.
tokenizer=AutoTokenizer.from_pretrained(MODEL,trust_remote_code=True,use_fast=True)  # 토크나이저를 로드합니다.
if tokenizer.pad_token_id is None: tokenizer.pad_token_id=tokenizer.eos_token_id  # 패딩 토큰을 보정합니다.
dtype=torch.float16 if torch.cuda.is_available() else torch.float32  # 장치별 자료형을 선택합니다.
model=AutoModelForCausalLM.from_pretrained(MODEL,torch_dtype=dtype,trust_remote_code=True,low_cpu_mem_usage=True)  # 베이스 모델을 로드합니다.
model.config.use_cache=False  # 학습 메모리 절약을 위해 캐시를 끕니다.
data=load_dataset('json',data_files={'train':str(BASE/'training/sample_train.jsonl')})['train']  # 학습 데이터를 읽습니다.
peft=LoraConfig(task_type=TaskType.CAUSAL_LM,r=16,lora_alpha=32,lora_dropout=0.05,bias='none',target_modules=['q_proj','k_proj','v_proj','o_proj','gate_proj','up_proj','down_proj'])  # LoRA 대상 계층을 설정합니다.
args=TrainingArguments(output_dir=str(OUT),num_train_epochs=3,per_device_train_batch_size=1,gradient_accumulation_steps=8,learning_rate=2e-4,logging_steps=1,save_strategy='epoch',fp16=torch.cuda.is_available(),report_to='none',remove_unused_columns=False)  # 학습 하이퍼파라미터를 정의합니다.
def format_example(example): return tokenizer.apply_chat_template(example['messages'],tokenize=False,add_generation_prompt=False)  # messages를 채팅 학습 문자열로 바꿉니다.
trainer=SFTTrainer(model=model,args=args,train_dataset=data,peft_config=peft,formatting_func=format_example)  # SFT 트레이너를 생성합니다.
trainer.train()  # LoRA 파인튜닝을 실행합니다.
trainer.save_model(str(OUT))  # 어댑터를 저장합니다.
tokenizer.save_pretrained(str(OUT))  # 토크나이저도 저장합니다.
