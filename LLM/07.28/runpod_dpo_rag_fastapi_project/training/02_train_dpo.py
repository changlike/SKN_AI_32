"""SFT 모델을 기준으로 LoRA DPO를 수행합니다."""
# GPU 연산과 최적화를 위해 torch를 가져옵니다.
import torch
# DPO 손실 함수 계산을 위해 functional을 가져옵니다.
import torch.nn.functional as F
# SFT 어댑터를 연결하기 위해 PeftModel을 가져옵니다.
from peft import PeftModel
# 모델과 토크나이저를 가져옵니다.
from transformers import AutoModelForCausalLM, AutoTokenizer
# 공통 유틸리티를 가져옵니다.
from training.common import ROOT, env, read_jsonl, seed_all, show_trainable

# prompt와 answer를 채팅 템플릿 문자열로 만듭니다.
def build_text(tokenizer, prompt: str, answer: str) -> tuple[str, str]:
    # 답변 전까지의 메시지입니다.
    head = [{'role':'system','content':'당신은 정확하고 친절한 한국어 AI 조교입니다.'},{'role':'user','content':prompt}]
    # 모델이 답변을 시작할 위치까지의 문자열입니다.
    prompt_text = tokenizer.apply_chat_template(head, tokenize=False, add_generation_prompt=True)
    # 실제 답변까지 포함한 전체 문자열입니다.
    full_text = tokenizer.apply_chat_template(head+[{'role':'assistant','content':answer}], tokenize=False, add_generation_prompt=False)
    # 두 문자열을 반환합니다.
    return prompt_text, full_text

# 답변 토큰 구간의 평균 로그확률을 계산합니다.
def sequence_logp(model, tokenizer, prompt: str, answer: str) -> torch.Tensor:
    # 프롬프트와 전체 대화를 만듭니다.
    prompt_text, full_text = build_text(tokenizer, prompt, answer)
    # 답변 시작 토큰 위치를 계산합니다.
    prompt_len = tokenizer(prompt_text, return_tensors='pt', truncation=True, max_length=1024, add_special_tokens=False)['input_ids'].shape[1]
    # 전체 대화를 토큰화합니다.
    batch = tokenizer(full_text, return_tensors='pt', truncation=True, max_length=1024, add_special_tokens=False)
    # 모델 장치를 확인합니다.
    device = next(model.parameters()).device
    # 입력 텐서를 모델 장치로 이동합니다.
    ids = batch['input_ids'].to(device)
    # attention mask를 모델 장치로 이동합니다.
    mask = batch['attention_mask'].to(device)
    # 다음 토큰 로짓을 계산합니다.
    logits = model(input_ids=ids, attention_mask=mask).logits[:, :-1]
    # 로짓을 로그확률로 변환합니다.
    log_probs = F.log_softmax(logits, dim=-1)
    # 실제 다음 토큰 ID를 정답으로 사용합니다.
    targets = ids[:, 1:]
    # 정답 토큰의 로그확률만 선택합니다.
    selected = log_probs.gather(-1, targets.unsqueeze(-1)).squeeze(-1)
    # causal shift를 반영한 답변 시작점을 계산합니다.
    start = max(int(prompt_len)-1, 0)
    # 답변 구간을 선택합니다.
    answer_scores = selected[:, start:]
    # 답변이 잘렸으면 안전한 큰 음수 값을 반환합니다.
    if answer_scores.numel() == 0:
        # 그래프 연결을 유지하는 상수 손실을 만듭니다.
        return logits.sum()*0 - 1e4
    # 길이 편향을 줄이기 위해 평균 로그확률을 반환합니다.
    return answer_scores.mean()

# DPO 전체 학습을 수행합니다.
def main() -> None:
    # 난수 시드를 고정합니다.
    seed_all()
    # 원본 모델 ID를 읽습니다.
    base_id = env('BASE_MODEL','Qwen/Qwen2.5-0.5B-Instruct')
    # SFT 어댑터 경로를 계산합니다.
    sft = ROOT / env('SFT_ADAPTER','outputs/sft_adapter')
    # DPO 출력 경로를 계산합니다.
    output = ROOT / env('DPO_ADAPTER','outputs/dpo_adapter')
    # 출력 폴더를 생성합니다.
    output.mkdir(parents=True, exist_ok=True)
    # SFT 토크나이저를 로드합니다.
    tokenizer = AutoTokenizer.from_pretrained(sft, trust_remote_code=True)
    # 패딩 토큰을 보장합니다.
    tokenizer.pad_token_id = tokenizer.pad_token_id or tokenizer.eos_token_id
    # GPU에서 float16을 사용합니다.
    dtype = torch.float16 if torch.cuda.is_available() else torch.float32

    # 학습할 정책 모델의 원본을 로드합니다.
    policy_base = AutoModelForCausalLM.from_pretrained(base_id, torch_dtype=dtype, device_map='auto' if torch.cuda.is_available() else None, trust_remote_code=True, token=env('HF_TOKEN','') or None)
    # 정책 모델에 SFT 어댑터를 학습 가능 상태로 연결합니다.
    policy = PeftModel.from_pretrained(policy_base, sft, is_trainable=True)
    # KV 캐시를 끕니다.
    policy.config.use_cache = False
    # 정책 모델의 학습 파라미터를 출력합니다.
    show_trainable(policy)

    # 고정 기준 모델의 원본을 별도로 로드합니다.
    ref_base = AutoModelForCausalLM.from_pretrained(base_id, torch_dtype=dtype, device_map='auto' if torch.cuda.is_available() else None, trust_remote_code=True, token=env('HF_TOKEN','') or None)
    # 기준 모델에 같은 SFT 어댑터를 학습 불가 상태로 연결합니다.
    reference = PeftModel.from_pretrained(ref_base, sft, is_trainable=False)
    # 기준 모델을 평가 모드로 전환합니다.
    reference.eval()
    # 기준 모델 파라미터를 모두 동결합니다.
    for parameter in reference.parameters():
        # gradient 계산을 끕니다.
        parameter.requires_grad = False

    # DPO 선호 데이터를 읽습니다.
    rows = read_jsonl(ROOT/'data/dpo_train.jsonl')
    # 학습 가능한 LoRA 파라미터만 최적화합니다.
    optimizer = torch.optim.AdamW((p for p in policy.parameters() if p.requires_grad), lr=5e-6, weight_decay=0.01)
    # 기준 모델에서 벗어나는 정도를 조절하는 beta입니다.
    beta = 0.1
    # 정책 모델을 학습 모드로 전환합니다.
    policy.train()
    # 작은 예제 데이터로 3 epoch 반복합니다.
    for epoch in range(3):
        # 모든 선호 쌍을 순회합니다.
        for step, row in enumerate(rows, 1):
            # 이전 gradient를 초기화합니다.
            optimizer.zero_grad(set_to_none=True)
            # 정책 모델의 chosen 로그확률을 계산합니다.
            pi_c = sequence_logp(policy, tokenizer, row['prompt'], row['chosen'])
            # 정책 모델의 rejected 로그확률을 계산합니다.
            pi_r = sequence_logp(policy, tokenizer, row['prompt'], row['rejected'])
            # 기준 모델은 gradient 없이 점수만 계산합니다.
            with torch.no_grad():
                # 기준 모델의 chosen 로그확률입니다.
                ref_c = sequence_logp(reference, tokenizer, row['prompt'], row['chosen'])
                # 기준 모델의 rejected 로그확률입니다.
                ref_r = sequence_logp(reference, tokenizer, row['prompt'], row['rejected'])
            # 정책 선호 마진과 기준 선호 마진의 차이를 계산합니다.
            advantage = (pi_c-pi_r) - (ref_c-ref_r)
            # chosen 마진이 커지도록 DPO log-sigmoid 손실을 계산합니다.
            loss = -F.logsigmoid(beta*advantage)
            # LoRA 파라미터 gradient를 계산합니다.
            loss.backward()
            # gradient 폭주를 방지합니다.
            torch.nn.utils.clip_grad_norm_(policy.parameters(), 1.0)
            # 파라미터를 한 단계 갱신합니다.
            optimizer.step()
            # 진행 상황을 출력합니다.
            print(f'epoch={epoch+1} step={step} loss={loss.item():.6f} margin={(pi_c-pi_r).item():.6f}')
    # DPO 어댑터를 저장합니다.
    policy.save_pretrained(output)
    # 토크나이저를 저장합니다.
    tokenizer.save_pretrained(output)
    # 완료 경로를 출력합니다.
    print(f'DPO 저장 완료: {output}')

# 직접 실행할 때만 main을 호출합니다.
if __name__ == '__main__':
    # DPO 학습을 시작합니다.
    main()
