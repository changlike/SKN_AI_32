"""RAG 근거 기반 답변과 선택적 로컬 파인튜닝 모델 추론을 제공합니다."""
from pathlib import Path  # 로컬 모델 파일 구성을 확인합니다.
from threading import Lock  # 모델 중복 로딩을 방지합니다.
import logging  # 로컬 모델 오류를 기록합니다.
import re  # 근거 문장에서 질문 관련 문장을 선택합니다.
from app.config import settings  # 모델 설정을 가져옵니다.

logger = logging.getLogger(__name__)  # 현재 모듈 전용 로거입니다.

class FineTunedLlmService:
    """기본은 근거 추출형 답변이며, 설정 시 로컬 모델을 추가로 사용합니다."""
    def __init__(self) -> None:
        self._tokenizer = None  # 선택적으로 로딩할 토크나이저입니다.
        self._model = None  # 선택적으로 로딩할 로컬 모델입니다.
        self._mode = "rag_extractive"  # 모델 파일 없이도 실행되는 기본 모드입니다.
        self._load_error: str | None = None  # 마지막 모델 오류를 저장합니다.
        self._lock = Lock()  # 최초 모델 로딩을 보호합니다.

    @property
    def mode(self) -> str:
        return self._mode  # 현재 답변 생성 모드를 반환합니다.

    @property
    def load_error(self) -> str | None:
        return self._load_error  # 마지막 모델 로딩 오류를 반환합니다.

    def _valid_model(self, path: Path) -> bool:
        has_config = (path / "config.json").is_file() or (path / "adapter_config.json").is_file()  # 전체 모델 또는 LoRA 설정 파일을 확인합니다.
        has_weight = any(path.glob("*.safetensors")) or any(path.glob("*.bin"))  # 실제 가중치 파일이 하나 이상 있는지 확인합니다.
        return has_config and has_weight  # 설정과 가중치가 모두 있어야 유효한 모델입니다.

    def _device(self) -> str:
        if settings.LLM_DEVICE in {"cpu", "cuda"}:
            return settings.LLM_DEVICE  # 사용자가 지정한 장치를 그대로 사용합니다.
        import torch  # CUDA 사용 가능 여부를 확인합니다.
        return "cuda" if torch.cuda.is_available() else "cpu"  # GPU가 있으면 CUDA를 선택합니다.

    def _load_optional_model(self) -> None:
        if not settings.USE_LOCAL_MODEL or self._model is not None:
            return  # 로컬 모델 사용이 꺼져 있거나 이미 로딩된 경우 종료합니다.
        with self._lock:
            if self._model is not None:
                return  # 다른 요청이 먼저 모델을 로딩했는지 확인합니다.
            path = settings.LOCAL_MODEL_PATH  # 환경 설정의 모델 경로를 가져옵니다.
            if not self._valid_model(path):
                self._mode = "rag_extractive"  # 모델이 없으면 RAG 근거 추출 모드를 유지합니다.
                self._load_error = f"유효한 로컬 모델이 없습니다: {path}"  # 상태 API에 원인을 기록합니다.
                logger.warning(self._load_error)  # 서버 터미널에 안내를 기록합니다.
                return
            try:
                import torch  # 모델 자료형과 추론에 사용합니다.
                from transformers import AutoModelForCausalLM, AutoTokenizer  # Hugging Face 모델 클래스를 가져옵니다.
                device = self._device()  # 실행 장치를 선택합니다.
                dtype = torch.float16 if device == "cuda" else torch.float32  # GPU에서는 FP16, CPU에서는 FP32를 사용합니다.
                self._tokenizer = AutoTokenizer.from_pretrained(str(path), trust_remote_code=True)  # 로컬 토크나이저를 로딩합니다.
                self._model = AutoModelForCausalLM.from_pretrained(str(path), torch_dtype=dtype, trust_remote_code=True, low_cpu_mem_usage=True)  # 로컬 모델을 로딩합니다.
                self._model.to(device).eval()  # 모델을 장치로 이동하고 평가 모드로 변경합니다.
                self._mode = "local_finetuned_model"  # 정상 모델 모드를 기록합니다.
                self._load_error = None  # 이전 오류를 제거합니다.
            except Exception as exc:
                self._tokenizer = None  # 불완전한 토크나이저를 제거합니다.
                self._model = None  # 불완전한 모델을 제거합니다.
                self._mode = "rag_extractive"  # 서비스 중단 없이 근거 추출 모드로 돌아갑니다.
                self._load_error = f"{type(exc).__name__}: {exc}"  # 오류 원인을 저장합니다.
                logger.exception("로컬 모델 로딩 실패: %s", exc)  # 상세 오류를 터미널에 기록합니다.

    def _extractive_answer(self, question: str, contexts: list[dict]) -> str:
        if not contexts:
            return "제공된 근거 문서에서 관련 내용을 찾지 못했습니다. data/docs 폴더의 문서를 확인한 뒤 RAG 인덱스를 다시 생성해 주세요."  # 근거가 없을 때 추측하지 않습니다.
        question_terms = set(re.findall(r"[가-힣]{2,}|[A-Za-z0-9]{2,}", question.lower()))  # 질문의 핵심 단어를 추출합니다.
        candidates: list[tuple[int, str, dict]] = []  # 관련 문장과 출처를 저장합니다.
        for context in contexts:
            sentences = re.split(r"(?<=[.!?])\s+|(?<=다\.)\s*", context["text"])  # 문서 조각을 문장 단위로 나눕니다.
            for sentence in sentences:
                clean = sentence.strip()  # 문장 앞뒤 공백을 제거합니다.
                if len(clean) < 12:
                    continue  # 너무 짧은 조각은 답변 후보에서 제외합니다.
                sentence_terms = set(re.findall(r"[가-힣]{2,}|[A-Za-z0-9]{2,}", clean.lower()))  # 문장의 단어를 추출합니다.
                overlap = len(question_terms & sentence_terms)  # 질문과 문장이 공유하는 단어 수를 계산합니다.
                candidates.append((overlap, clean, context))  # 점수와 문장, 출처를 함께 저장합니다.
        candidates.sort(key=lambda item: (item[0], item[2]["score"]), reverse=True)  # 질문 관련성과 검색 점수 순으로 정렬합니다.
        selected: list[tuple[str, dict]] = []  # 최종 답변에 사용할 문장을 저장합니다.
        seen: set[str] = set()  # 동일 문장 중복을 방지합니다.
        for _, sentence, context in candidates:
            key = sentence[:100]  # 문장 앞부분을 중복 판별 키로 사용합니다.
            if key in seen:
                continue  # 이미 선택한 문장은 건너뜁니다.
            seen.add(key)  # 선택한 문장으로 기록합니다.
            selected.append((sentence, context))  # 답변 문장과 출처를 추가합니다.
            if len(selected) >= 3:
                break  # 최대 세 문장만 선택해 간결한 답변을 만듭니다.
        if not selected:
            selected = [(contexts[0]["text"][:700], contexts[0])]  # 문장 분리가 실패하면 첫 근거 본문을 사용합니다.
        answer_body = "\n".join(f"- {sentence}" for sentence, _ in selected)  # 선택된 문장을 목록 형태로 구성합니다.
        source_labels: list[str] = []  # 중복 없는 출처 표시를 저장합니다.
        for _, context in selected:
            page = f" {context['page']}페이지" if context.get("page") else ""  # PDF일 때 페이지 번호를 표시합니다.
            label = f"{context['source']}{page}"  # 파일명과 페이지를 결합합니다.
            if label not in source_labels:
                source_labels.append(label)  # 같은 출처는 한 번만 추가합니다.
        return f"제공된 근거 문서에서 확인된 내용입니다.\n\n{answer_body}\n\n근거: {', '.join(source_labels)}"  # 답변과 출처를 함께 반환합니다.

    def generate(self, question: str, contexts: list[dict]) -> str:
        self._load_optional_model()  # 설정된 경우에만 로컬 모델을 준비합니다.
        if self._model is None or self._tokenizer is None:
            return self._extractive_answer(question, contexts)  # 기본 실행은 근거 문장만으로 안전하게 답합니다.
        import torch  # 로컬 모델 추론 시 그래디언트를 끄기 위해 사용합니다.
        context_text = "\n\n".join(f"[{item['source']} {item.get('page') or '-'}페이지]\n{item['text']}" for item in contexts) or "검색 근거 없음"  # 검색 근거를 하나의 프롬프트로 구성합니다.
        prompt = f"당신은 한국어 고객 상담원입니다. 다음 근거에 있는 내용만 사용하고 추측하지 마세요.\n\n{context_text}\n\n질문: {question}\n답변:"  # 근거 제한형 프롬프트를 작성합니다.
        inputs = self._tokenizer(prompt, return_tensors="pt", truncation=True, max_length=4096)  # 프롬프트를 토큰으로 변환합니다.
        device = next(self._model.parameters()).device  # 모델이 올라간 실제 장치를 확인합니다.
        inputs = {key: value.to(device) for key, value in inputs.items()}  # 입력 텐서를 모델 장치로 이동합니다.
        with torch.inference_mode():
            output = self._model.generate(**inputs, max_new_tokens=settings.MAX_NEW_TOKENS, do_sample=False, repetition_penalty=1.08)  # 결정적 방식으로 답변을 생성합니다.
        answer_ids = output[0][inputs["input_ids"].shape[1]:]  # 입력 토큰을 제외한 생성 부분만 선택합니다.
        answer = self._tokenizer.decode(answer_ids, skip_special_tokens=True).strip()  # 토큰을 한국어 문자열로 변환합니다.
        return answer or self._extractive_answer(question, contexts)  # 빈 출력이면 근거 추출 답변으로 대체합니다.
