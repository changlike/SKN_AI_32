"""Base, SFT, DPO 모델을 동일 데이터로 비교 평가합니다."""
# 결과 저장을 위해 json을 가져옵니다.
import json
# 지연 시간 측정을 위해 time을 가져옵니다.
import time
# 동적 모듈 로딩을 위해 import_module을 가져옵니다.
from importlib import import_module
# GPU 추론을 위해 torch를 가져옵니다.
import torch
# SFT/DPO 어댑터 연결을 위해 PeftModel을 가져옵니다.
from peft import PeftModel
# ROUGE-L 계산기를 가져옵니다.
from rouge_score import rouge_scorer
# 모델과 토크나이저를 가져옵니다.
from transformers import AutoModelForCausalLM, AutoTokenizer
# 공통 설정을 가져옵니다.
from training.common import ROOT, env, read_jsonl, seed_all
# 숫자로 시작하는 DPO 파일의 로그확률 함수를 동적으로 가져옵니다.
sequence_logp = import_module('training.02_train_dpo').sequence_logp

# 평가 대상 모델을 로드합니다.
def load(kind: str):
    # 원본 모델 ID를 읽습니다.
    base_id = env('BASE_MODEL','Qwen/Qwen2.5-0.5B-Instruct')
    # GPU에서는 float16을 사용합니다.
    dtype = torch.float16 if torch.cuda.is_available() else torch.float32
    # DPO 병합 모델이 존재하면 직접 로드합니다.
    merged = ROOT / env('MERGED_MODEL','outputs/dpo_merged')
    # DPO 평가이며 병합 경로가 있으면 일반 모델로 읽습니다.
    if kind == 'dpo' and merged.exists():
        # 병합 모델 토크나이저를 로드합니다.
        tokenizer = AutoTokenizer.from_pretrained(merged, trust_remote_code=True)
        # 병합 모델을 로드합니다.
        model = AutoModelForCausalLM.from_pretrained(merged, torch_dtype=dtype, device_map='auto' if torch.cuda.is_available() else None, trust_remote_code=True)
        # 모델과 토크나이저를 반환합니다.
        return model, tokenizer
    # 원본 모델 토크나이저를 로드합니다.
    tokenizer = AutoTokenizer.from_pretrained(base_id, trust_remote_code=True, token=env('HF_TOKEN','') or None)
    # 패딩 토큰을 보장합니다.
    tokenizer.pad_token_id = tokenizer.pad_token_id or tokenizer.eos_token_id
    # 원본 모델을 로드합니다.
    base = AutoModelForCausalLM.from_pretrained(base_id, torch_dtype=dtype, device_map='auto' if torch.cuda.is_available() else None, trust_remote_code=True, token=env('HF_TOKEN','') or None)
    # Base 평가이면 원본 모델을 반환합니다.
    if kind == 'base':
        # 모델과 토크나이저를 반환합니다.
        return base, tokenizer
    # SFT 또는 DPO 어댑터 경로를 선택합니다.
    adapter = ROOT / (env('SFT_ADAPTER','outputs/sft_adapter') if kind == 'sft' else env('DPO_ADAPTER','outputs/dpo_adapter'))
    # 원본 모델에 평가용 어댑터를 연결합니다.
    return PeftModel.from_pretrained(base, adapter, is_trainable=False), tokenizer

# 하나의 질문에 결정적 답변을 생성합니다.
def generate(model, tokenizer, prompt: str):
    # 채팅 메시지를 구성합니다.
    messages = [{'role':'system','content':'당신은 정확하고 친절한 한국어 AI 조교입니다.'},{'role':'user','content':prompt}]
    # 채팅 템플릿을 적용합니다.
    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    # 입력을 토큰화합니다.
    batch = tokenizer(text, return_tensors='pt', truncation=True, max_length=1024)
    # 모델 장치로 입력을 이동합니다.
    batch = {k:v.to(next(model.parameters()).device) for k,v in batch.items()}
    # 시작 시각을 기록합니다.
    started = time.perf_counter()
    # gradient 없이 greedy generation을 수행합니다.
    with torch.inference_mode():
        # 최대 128 토큰을 생성합니다.
        output = model.generate(**batch, max_new_tokens=128, do_sample=False, pad_token_id=tokenizer.pad_token_id, eos_token_id=tokenizer.eos_token_id)
    # 지연 시간을 계산합니다.
    latency = time.perf_counter()-started
    # 입력 이후의 신규 토큰을 선택합니다.
    new_ids = output[0,batch['input_ids'].shape[1]:]
    # 답변 문자열과 지연 시간을 반환합니다.
    return tokenizer.decode(new_ids, skip_special_tokens=True).strip(), latency

# 한 모델의 전체 지표를 계산합니다.
def evaluate(kind: str, rows):
    # 모델과 토크나이저를 로드합니다.
    model, tokenizer = load(kind)
    # 모델을 평가 모드로 전환합니다.
    model.eval()
    # ROUGE-L 계산기를 만듭니다.
    rouge = rouge_scorer.RougeScorer(['rougeL'], use_stemmer=False)
    # 선호 정답 수를 초기화합니다.
    correct = 0
    # ROUGE 점수 목록입니다.
    rouge_values = []
    # 지연 시간 목록입니다.
    latencies = []
    # 상세 결과 목록입니다.
    details = []
    # 모든 평가 샘플을 순회합니다.
    for row in rows:
        # 로그확률 계산에서는 gradient를 끕니다.
        with torch.inference_mode():
            # chosen 점수를 계산합니다.
            chosen = float(sequence_logp(model, tokenizer, row['prompt'], row['chosen']).cpu())
            # rejected 점수를 계산합니다.
            rejected = float(sequence_logp(model, tokenizer, row['prompt'], row['rejected']).cpu())
        # chosen 점수가 높으면 정답으로 누적합니다.
        correct += int(chosen > rejected)
        # 실제 답변과 지연 시간을 생성합니다.
        prediction, latency = generate(model, tokenizer, row['prompt'])
        # ROUGE-L F1을 저장합니다.
        rouge_values.append(rouge.score(row['chosen'], prediction)['rougeL'].fmeasure)
        # 지연 시간을 저장합니다.
        latencies.append(latency)
        # 상세 샘플 결과를 저장합니다.
        details.append({'prompt':row['prompt'],'prediction':prediction,'chosen_logp':chosen,'rejected_logp':rejected})
    # 집계 지표를 반환합니다.
    return {'preference_accuracy':correct/max(len(rows),1),'rouge_l_f1':sum(rouge_values)/max(len(rows),1),'average_latency_seconds':sum(latencies)/max(len(rows),1),'details':details}

# 세 모델을 평가해 JSON으로 저장합니다.
def main() -> None:
    # 난수 시드를 고정합니다.
    seed_all()
    # 평가 데이터를 읽습니다.
    rows = read_jsonl(ROOT/'data/eval.jsonl')
    # 결과 디렉터리를 생성합니다.
    output = ROOT/'outputs/evaluation'
    # 상위 폴더까지 생성합니다.
    output.mkdir(parents=True, exist_ok=True)
    # Base, SFT, DPO 결과를 계산합니다.
    results = {kind:evaluate(kind, rows) for kind in ['base','sft','dpo']}
    # 한글을 유지한 JSON으로 저장합니다.
    (output/'results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    # 결과를 콘솔에도 출력합니다.
    print(json.dumps(results,ensure_ascii=False,indent=2))

# 직접 실행할 때만 main을 호출합니다.
if __name__ == '__main__':
    # 평가를 시작합니다.
    main()
