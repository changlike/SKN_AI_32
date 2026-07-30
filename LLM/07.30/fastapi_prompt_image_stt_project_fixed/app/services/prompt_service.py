"""
한국어 프롬프트를 영어로 번역하고 이미지 생성에 적합하게 보강합니다.
"""

# 한글 포함 여부와 불필요한 명령 표현을 검사하기 위해 re 모듈을 가져옵니다.
import re

# 여러 요청에서 번역 모델을 재사용하기 위해 Lock을 가져옵니다.
from threading import Lock

# 지연 로딩 모델 객체에 유연한 타입을 적용하기 위해 Any를 가져옵니다.
from typing import Any

# CUDA 사용 가능 여부를 확인하기 위해 torch를 가져옵니다.
import torch

# 프로젝트 환경 설정 객체를 가져옵니다.
from app.core.config import settings


# MarianMT 토크나이저를 한 번만 로딩하기 위한 캐시 변수를 선언합니다.
_translation_tokenizer: Any | None = None

# MarianMT 모델을 한 번만 로딩하기 위한 캐시 변수를 선언합니다.
_translation_model: Any | None = None

# 최초 번역 모델 로딩 시 중복 실행을 막기 위한 잠금 객체를 생성합니다.
_translation_lock = Lock()


# 한국어 또는 영어에서 사람을 의미하는 주요 표현을 정의합니다.
PERSON_TERMS: tuple[str, ...] = (
    "사람",
    "남자",
    "남성",
    "여자",
    "여성",
    "아이",
    "어린이",
    "소년",
    "소녀",
    "인물",
    "얼굴",
    "초상",
    "모델",
    "배우",
    "가족",
    "커플",
    "군중",
    "person",
    "people",
    "man",
    "woman",
    "boy",
    "girl",
    "child",
    "children",
    "human",
    "portrait",
    "face",
    "family",
    "couple",
    "crowd",
    "actor",
    "actress",
)


# 한국어 요청 문장에 자주 포함되는 이미지 생성 명령 표현을 정의합니다.
KOREAN_COMMAND_PATTERNS: tuple[str, ...] = (
    r"\s*이미지(?:를|로)?\s*생성(?:해|하여|해서)?\s*(?:줘|주세요|주시오|해줘|해주세요)?\s*$",
    r"\s*그림(?:을|으로)?\s*(?:그려|만들어)\s*(?:줘|주세요|주시오)?\s*$",
    r"\s*사진(?:을|으로)?\s*(?:만들어|생성해)\s*(?:줘|주세요|주시오)?\s*$",
    r"\s*(?:만들어|생성해|그려)\s*(?:줘|주세요|주시오)\s*$",
)


# 프롬프트에 한글 문자가 포함되어 있는지 확인합니다.
def contains_korean(text: str) -> bool:
    """문자열에 한글 음절 또는 자모가 포함되어 있으면 True를 반환합니다."""

    # 정규표현식으로 한글 음절 및 자모 범위를 검색합니다.
    return re.search(r"[가-힣ㄱ-ㅎㅏ-ㅣ]", text) is not None


# 한국어 문장 끝에 붙은 단순 생성 명령을 제거합니다.
def remove_korean_command_phrase(text: str) -> str:
    """핵심 장면 설명은 유지하고 단순 생성 명령 표현만 제거합니다."""

    # 앞뒤 공백을 제거한 문자열을 초기 결과로 저장합니다.
    cleaned_text = text.strip()

    # 준비한 각 명령 패턴을 순서대로 적용합니다.
    for pattern in KOREAN_COMMAND_PATTERNS:
        # 현재 패턴과 일치하는 문장 끝부분을 빈 문자열로 교체합니다.
        cleaned_text = re.sub(
            pattern,
            "",
            cleaned_text,
            flags=re.IGNORECASE,
        ).strip()

    # 명령을 모두 제거한 뒤 문장이 비었는지 확인합니다.
    if not cleaned_text:
        # 핵심 내용이 모두 제거되었다면 원본을 유지합니다.
        return text.strip()

    # 정리된 핵심 프롬프트를 반환합니다.
    return cleaned_text


# 프롬프트가 사람을 명시적으로 요청하는지 확인합니다.
def requests_people(text: str) -> bool:
    """프롬프트에 인물 관련 단어가 하나라도 포함되면 True를 반환합니다."""

    # 대소문자 차이를 없애기 위해 문장을 소문자로 변환합니다.
    lowered_text = text.lower()

    # 정의된 모든 인물 관련 단어를 순서대로 확인합니다.
    return any(term in lowered_text for term in PERSON_TERMS)


# 번역 모델과 토크나이저를 로딩하여 반환합니다.
def get_translation_components() -> tuple[Any, Any]:
    """MarianMT 번역 모델과 토크나이저를 최초 한 번 로딩합니다."""

    # 함수 내부에서 전역 캐시 변수를 수정한다고 선언합니다.
    global _translation_tokenizer, _translation_model

    # 두 객체가 모두 이미 생성되어 있는지 확인합니다.
    if (
        _translation_tokenizer is not None
        and _translation_model is not None
    ):
        # 캐시된 토크나이저와 모델을 반환합니다.
        return _translation_tokenizer, _translation_model

    # 여러 요청이 동시에 모델을 내려받거나 로딩하지 못하도록 잠금을 획득합니다.
    with _translation_lock:
        # 잠금을 기다리는 동안 다른 요청이 로딩을 완료했는지 다시 확인합니다.
        if (
            _translation_tokenizer is not None
            and _translation_model is not None
        ):
            # 이미 생성된 객체를 반환합니다.
            return _translation_tokenizer, _translation_model

        # 실제 번역 요청 시점에 필요한 Transformers 클래스를 가져옵니다.
        from transformers import MarianMTModel, MarianTokenizer

        # 환경 설정에 지정된 모델의 토크나이저를 내려받아 로딩합니다.
        _translation_tokenizer = MarianTokenizer.from_pretrained(
            settings.translation_model_id
        )

        # 환경 설정에 지정된 MarianMT 모델을 내려받아 로딩합니다.
        _translation_model = MarianMTModel.from_pretrained(
            settings.translation_model_id
        )

        # CUDA GPU를 사용할 수 있으면 번역 모델을 GPU로 이동합니다.
        if torch.cuda.is_available():
            # 번역 모델을 CUDA 장치로 이동합니다.
            _translation_model.to("cuda")

        # 추론 시 Dropout이 적용되지 않도록 평가 모드로 전환합니다.
        _translation_model.eval()

        # 완성된 토크나이저와 모델을 반환합니다.
        return _translation_tokenizer, _translation_model


# 한국어 문장을 영어로 번역합니다.
def translate_korean_to_english(text: str) -> str:
    """MarianMT를 이용해 한국어 핵심 장면 설명을 영어로 번역합니다."""

    # 번역 모델과 토크나이저를 가져옵니다.
    tokenizer, model = get_translation_components()

    # 번역 모델이 위치한 실제 실행 장치를 확인합니다.
    model_device = next(model.parameters()).device

    # 한국어 문장을 모델 입력 토큰으로 변환합니다.
    encoded = tokenizer(
        [text],
        return_tensors="pt",
        padding=True,
        truncation=True,
        max_length=256,
    )

    # 토큰 텐서를 번역 모델과 같은 장치로 이동합니다.
    encoded = {
        key: value.to(model_device)
        for key, value in encoded.items()
    }

    # 번역은 역전파가 필요 없으므로 기울기 계산을 비활성화합니다.
    with torch.no_grad():
        # 의미 보존을 위해 beam search를 사용하여 영어 토큰을 생성합니다.
        generated_tokens = model.generate(
            **encoded,
            num_beams=5,
            max_new_tokens=256,
            early_stopping=True,
        )

    # 생성된 토큰을 사람이 읽을 수 있는 영어 문자열로 변환합니다.
    translated_text = tokenizer.batch_decode(
        generated_tokens,
        skip_special_tokens=True,
    )[0].strip()

    # 빈 번역 결과가 반환되었는지 확인합니다.
    if not translated_text:
        # 번역 실패 시 명확한 예외를 발생시킵니다.
        raise RuntimeError("한국어 프롬프트를 영어로 번역하지 못했습니다.")

    # 번역된 영어 문장을 반환합니다.
    return translated_text


# 번역된 장면 설명을 이미지 모델용 프롬프트로 보강합니다.
def enhance_prompt(translated_prompt: str) -> str:
    """핵심 피사체와 구도를 강조하여 무관한 이미지 생성을 줄입니다."""

    # 앞뒤 공백과 문장 끝의 불필요한 마침표를 정리합니다.
    subject = translated_prompt.strip().rstrip(".")

    # 자동 보강 기능이 꺼져 있는지 확인합니다.
    if not settings.enable_prompt_enhancement:
        # 보강하지 않은 번역 프롬프트를 그대로 반환합니다.
        return subject

    # 핵심 장면을 반복적으로 명확히 지시하는 영어 프롬프트를 구성합니다.
    enhanced_prompt = (
        f"{subject}. "
        f"The primary subject is exactly: {subject}. "
        "Accurately depict only the requested subject and environment. "
        "The primary subject must be clearly visible, recognizable, "
        "and placed near the center of the composition. "
        "Coherent scene, natural proportions, detailed environment, "
        "high visual quality, realistic lighting, sharp focus. "
        "Do not replace the requested subject with unrelated objects."
    )

    # 완성된 보강 프롬프트를 반환합니다.
    return enhanced_prompt


# 사용자가 지정한 Negative prompt에 자동 억제 항목을 결합합니다.
def build_negative_prompt(
    original_prompt: str,
    translated_prompt: str,
    user_negative_prompt: str,
) -> str:
    """무관한 인물과 이미지 품질 저하 요소를 자동으로 억제합니다."""

    # 사용자가 입력한 Negative prompt를 앞뒤 공백 제거 후 저장합니다.
    negative_parts: list[str] = []

    # 사용자가 Negative prompt를 입력했는지 확인합니다.
    if user_negative_prompt.strip():
        # 사용자 입력을 첫 번째 억제 조건으로 추가합니다.
        negative_parts.append(user_negative_prompt.strip())

    # 기본적으로 억제할 무관한 구성과 품질 저하 요소를 추가합니다.
    negative_parts.append(
        "unrelated subject, wrong subject, random composition, "
        "duplicate objects, cropped primary subject"
    )

    # 사람 자동 억제 기능이 활성화되어 있는지 확인합니다.
    if settings.prevent_unrequested_people:
        # 원문과 번역문을 결합하여 사람 요청 여부를 확인합니다.
        combined_prompt = f"{original_prompt} {translated_prompt}"

        # 사용자가 사람을 요청하지 않았는지 확인합니다.
        if not requests_people(combined_prompt):
            # 무관한 인물 생성을 억제하는 단어를 추가합니다.
            negative_parts.append(
                "person, people, human, man, woman, boy, girl, child, "
                "face, portrait, body, crowd, celebrity"
            )

    # 중복된 항목을 입력 순서대로 제거합니다.
    unique_parts = list(dict.fromkeys(negative_parts))

    # 각 억제 문장을 쉼표로 연결하여 반환합니다.
    return ", ".join(unique_parts)


# 원본 프롬프트를 번역하고 보강한 모든 결과를 반환합니다.
def prepare_prompt(
    original_prompt: str,
    user_negative_prompt: str,
) -> dict[str, str | bool]:
    """원본, 정리, 번역, 보강 및 최종 Negative prompt를 생성합니다."""

    # 사용자 프롬프트의 앞뒤 공백을 제거합니다.
    stripped_prompt = original_prompt.strip()

    # 빈 프롬프트인지 확인합니다.
    if not stripped_prompt:
        # 빈 문장은 이미지 생성에 사용할 수 없으므로 오류를 발생시킵니다.
        raise ValueError("이미지 생성 프롬프트가 비어 있습니다.")

    # 프롬프트에 한글이 포함되어 있는지 확인합니다.
    korean_detected = contains_korean(stripped_prompt)

    # 한글 프롬프트이면 끝의 단순 명령 표현을 제거합니다.
    cleaned_prompt = (
        remove_korean_command_phrase(stripped_prompt)
        if korean_detected
        else stripped_prompt
    )

    # 한글 자동 번역이 필요한지 확인합니다.
    if korean_detected and settings.enable_prompt_translation:
        # 정리된 한국어 핵심 프롬프트를 영어로 번역합니다.
        translated_prompt = translate_korean_to_english(cleaned_prompt)
    else:
        # 영어 프롬프트이거나 번역이 꺼져 있으면 정리된 문장을 그대로 사용합니다.
        translated_prompt = cleaned_prompt

    # 이미지 모델이 핵심 주제를 더 잘 따르도록 영어 프롬프트를 보강합니다.
    enhanced_prompt = enhance_prompt(translated_prompt)

    # 사용자 Negative prompt와 자동 억제 조건을 결합합니다.
    final_negative_prompt = build_negative_prompt(
        original_prompt=stripped_prompt,
        translated_prompt=translated_prompt,
        user_negative_prompt=user_negative_prompt,
    )

    # 화면 표시, 저장 및 실제 추론에 사용할 모든 프롬프트 정보를 반환합니다.
    return {
        "original_prompt": stripped_prompt,
        "cleaned_prompt": cleaned_prompt,
        "translated_prompt": translated_prompt,
        "enhanced_prompt": enhanced_prompt,
        "final_negative_prompt": final_negative_prompt,
        "korean_detected": korean_detected,
    }
