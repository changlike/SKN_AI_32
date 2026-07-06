"""학습된 모델을 불러와 영어 <-> 한국어 번역을 수행하는 파일입니다."""

import re
import torch
from src.config import MODEL_PATH, META_PATH, EMBED_SIZE, NUM_HEADS, NUM_LAYERS, MAX_OUTPUT_LEN, SOS_TOKEN, UNK_TOKEN, EOS_TOKEN, DATA_PATH
from src.data_utils import normalize_text, encode_text
from src.model import TransformerTranslator

def detect_language(text: str) -> str:
    """입력 문장에 한글이 포함되어 있으면 ko, 그렇지 않으면 en으로 판단합니다."""
    # 정규표현식으로 한글 음절 범위가 포함되어 있는지 검사함
    if re.search(r"[가-힣]", text):
        # 한글이 하나라도 있으면 한국어 문장으로 판단함
        return "ko"
    # if --------------------
    # 한글이 없으면 영어 문장으로 판단함
    return "en"
# def -------------------------------------------------------------------------

def build_directional_source(text: str, source_lang: str) -> str:
    """영어 입력이면 한국어로 번역하라는 방향 토큰을 붙입니다."""
    if source_lang == "en":
        return "<EN2KO>" + normalize_text(text)
    # 한국어이면 영어로 번역하라는 방향 토큰을 입력문장 앞에 붙임
    return "<KO2EN>" + normalize_text(text)
# def -----------------------------------------

def load_model():
    """저장된 모델 가중치와 문자 사전을 불러옵니다."""
    # 모델 메타 파일이나 가중치 파일이 없으면, 학습을 먼저 실행하도록 함
    if not MODEL_PATH.exists() or not META_PATH.exists():
        raise FileNotFoundError("학습된 모델 파일이 없습니다. 먼저 python -m src.train 명령을 실행하세요.")
    # CPU 환경에서도 안전하게 불러오기 위해 map_location을 CPU로 지정함
    meta = torch.load(META_PATH, map_location="cpu")
    # 저장된 문자 -> 정수 사전을 가져옴
    char2idx = meta["char2idx"]
    # 저장된 숫자 -> 문자 사전을 가져옴
    idx2char = meta["idx2char"]
    # 저장된 사전 크기에 맞춰 모델 객체를 생성함
    model= TransformerTranslator(
        len(char2idx),
        meta.get("embed_size", EMBED_SIZE),
        meta.get("num_heads", NUM_HEADS),
        meta.get("num_layers", NUM_LAYERS),
    )
    # 학습된 가중치를 모델에 주입함
    model.load_state_dict(torch.load(MODEL_PATH, map_location="cpu"))
    # 추론에서는 dropout이나 batchnorm이 학습모드로 동작하지 않도록 평가모드로 전환함
    model.eval()
    # 추론에 필요한 모델과 사전을 반환합
    return model, char2idx, idx2char
# def ---------------------------------------

def load_exact_dictionary():
    """학습 데이터에 있는 문장은 정확한 번역을 우선하기 위해 딕셔너리로 읽습니다."""
    # pandas 의존을 줄이기 위해 csv 모듈을 사용합니다.
    import csv
    # 정확 매칭 번역을 저장할 딕셔너리 생성함
    mapping = {}
    # csv 파일을 utf-8 인코딩으로 엽니다.
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        # DictReader는 첫 줄의 en, ko 컬럼명을 기준으로 행을 딕셔너리로 읽습니다.
        reader = csv.DictReader(f)
        # 각 번역 쌍을 순회함
        for row in reader:
            # 영어 문장을 정리함
            en = normalize_text(row["en"])
            # 한국어 문장을 정리함
            ko = normalize_text(row["ko"])
            # 영어 입력에 대한 한국어 번역을 등록함
            mapping[("en", en)] = ko
            # 한국어 입력에 대한 영어 번역을 등록함
            mapping[("ko", ko)] = en
        # for ---------------------------------------------------
    # with ----------------------------------------------------------
    # 정확 매칭 딕셔너리를 반환함
    return mapping

def translate(text: str, model= None, char2idx=None, idx2char=None) -> str:
    """입력 문장을 자동으로 방향 판별하여 번역합니다."""
    # 빈 문장이면 번역할 수 없으므로 안내문구를 반환함
    if not text or not text.strip():
        return "번역할 문장을 입력하세요."

    # 입력 언어를 자동으로 판단함
    source_lang = detect_language(text)
    # 학습 데이터 문장을 정확히 번역하기 위해 사전을 사용함
    exact_dict = load_exact_dictionary()
    # 정리된 입력 문장을 기준으로 정확 매칭을 시도함
    exact_key = (source_lang, normalize_text(text))
    # 정확 매칭 결과가 있으면 바로 반환함
    if exact_key in exact_dict:
        return exact_dict[exact_key]

    # 모델 객체가 전달되지 않았다면 저장된 모델을 불러옵니다.
    if model is None or char2idx is None or idx2char is None:
        model, char2idx, idx2char = load_model()

    # 번역 방향 토큰을 포함한 인코더 입력 문자열을 만듭니다.
    source_text = build_directional_source(text, source_lang)
    # 입력 문장을 정수 인덱스 리스트로 변환합니다.
    source_idx = encode_text(source_text, char2idx, add_eos=True)
    # 모델 입력 형태 [배치, 시간]에 맞추기 위해 배치 차원을 추가함
    source_tensor = torch.tensor(source_idx, dtype=torch.long).unsqueeze(0)
    # 기울기 계산은 끔
    with torch.no_grad():
        # 입력 문장을 인코더가 읽어 글자별 문맥 벡터 전체를 만듦 (은닉상태 1개가 아님)
        encoder_output = model.encoder(source_tensor)

        # 지금까지 생성한 글자들을 담는 리스트. 디코더 시작 토큰(SOS)으로 시작함
        generated = [char2idx[SOS_TOKEN]]
        # 생성된 문자를 저장할 리스트
        result_chars = []

        # 최대 출력 길이만큼 한글자씩 생성합니다.
        for _ in range(MAX_OUTPUT_LEN):
            # 지금까지 만든 글자 전체를 매번 다시 입력으로 만듦 (자기회귀 생성)
            decoder_input = torch.tensor([generated], dtype=torch.long)
            # 현재 길이만큼 미래 가림막 생성 (뒷글자 커닝 방지)
            tgt_len = decoder_input.size(1)

            tgt_mask = torch.nn.Transformer.generate_square_subsequent_mask(tgt_len)
            # 원문 출력 + 지금까지의 번역문 + 가림막으로 다음 글자 점수를 계산함
            logits = model.decoder(decoder_input, encoder_output, tgt_mask)
            # 가장 점수가 높은 문자 인덱스를 선택함
            next_id = int(torch.argmax(logits[:, -1, :], dim = -1).item())
            # 선택된 인덱스를 문자로 변환함
            next_char = idx2char.get(next_id, UNK_TOKEN)
            # EOS가 나오면 문장 생성이 끝난 것으로 보고 반복을 중단함
            if next_char == EOS_TOKEN:
                break

            # 특수 토큰은 화면에 출력하지 않습니다.
            if next_char not in {"<PAD>", SOS_TOKEN, UNK_TOKEN}:
                result_chars.append(next_char)
            # 방금 예측한 글자를 리스트에 이어붙임 (다음 루프에서 통째로 다시 입력됨)
            generated.append(next_id)
        # with ------------------------------------------
        # 생성된 문자들을 하나의 문자열로 합침
        result = "".join(result_chars).strip()

        # 모델이 아무 문자도 생성하지 못한 경우 안내 문구를 반환함
        if not result:
            return "번역 결과를 생성하지 못했습니다. 학습 데이터를 늘리거나 epoch를 증가시켜 주세요."
        # 최종 번역 결과를 반환함
        return result



