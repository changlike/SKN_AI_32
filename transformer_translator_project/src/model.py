"""PyTorch 기반 문자 단위 Transformer 번역 모델을 정의하는 파일입니다."""

import torch
import torch.nn as nn

from src.config import PAD_TOKEN

class PositionalEncoding(nn.Module):
    """각 글자 위치에 번호 벡터를 더해주는 계층"""

    def __init__(self, max_seq_len, embed_size):
        super().__init__()
        # 위치 번호 -> embed_size 벡터 (단어 대신 위치를 넣는 임베딩)
        self.pos_embedding = nn.Embedding(max_seq_len, embed_size)

    def forward(self, x):
        # x: (배치, 글자수, embed size)
        seq_len = x.size(1)
        positions = torch.arange(seq_len, device=x.device)
        pos_vec = self.pos_embedding(positions)
        return x + pos_vec

class Encoder(nn.Module):
    """입력 문장을 Self-Attention으로 읽어 글자별 문맥 벡터를 만드는 인코더입니다."""

    def __init__(self, vocab_size, embed_size, num_heads, num_layers):
        # 부모 클래스(nn.Module)의 초기화 기능을 실행합니다. (부모 생성자 실행)
        super().__init__()
        # 문자 인덱스를 밀집 벡터로 변환하는 임베딩 계층입니다.
        self.embedding = nn.Embedding(vocab_size, embed_size, padding_idx=0)
        # 방금 만든 위치 번호표 계층
        self.pos_encoding = PositionalEncoding(max_seq_len=64, embed_size=embed_size)

        layer = nn.TransformerEncoderLayer(
            d_model=embed_size,
            nhead=num_heads,
            dim_feedforward=embed_size*4,
            batch_first=True,
        )
        self.transformer = nn.TransformerEncoder(layer, num_layers=num_layers)


    def forward(self, source_idx):
        # 정수 인덱스 문장을 임베딩 벡터 시퀀스로 변환합니다.
        embedded = self.embedding(source_idx)
        embedded = self.pos_encoding(embedded)
        # Self-Attention을 여러 층 통과시켜 글자별 문맥 벡터를 만듭니다.
        outputs = self.transformer(embedded)
        return outputs
# class Encoder ---------------------------------------------

class Decoder(nn.Module):
    """인코더 출력과 지금까지의 번역문을 함께 보고 다음 글자를 예측하는 디코더입니다."""
    def __init__(self, vocab_size, embed_size, num_heads, num_layers):
        # 반드시 첫줄에 부모 생성자 호출함
        super().__init__()
        # 출력 언어의 문자 인덱스를 벡터로 바꾸기 위한 임베딩 계층
        self.embedding = nn.Embedding(vocab_size, embed_size, padding_idx=0)
        self.pos_encoding = PositionalEncoding(max_seq_len=64, embed_size=embed_size)

        layer = nn.TransformerDecoderLayer(
            d_model=embed_size,
            nhead=num_heads,
            dim_feedforward=embed_size*4,
            batch_first=True,
        )
        self.transformer = nn.TransformerDecoder(layer, num_layers=num_layers)

        self.fc = nn.Linear(embed_size, vocab_size)

    def forward(self, decoder_input_idx, encoder_outputs, tgt_mask):
        # 디코더 입력 글자 인덱스를 임베딩 벡터로 변환함
        embedded = self.embedding(decoder_input_idx)
        embedded = self.pos_encoding(embedded)

        # tgt=번역문(Self-Attention), memory=원문 인코더 출력(Cross-Attention), tgt_mask=미래 가림막
        outputs = self.transformer(embedded, encoder_outputs, tgt_mask)
        # 각 글자 위치의 출력 벡터를 전체 문자 사전 점수(logits)로 변환함
        logits = self.fc(outputs)
        # 예측한 문자별 점수를 반환함 (hidden 없음 - Transformer는 은닉상태를 이어받지 않음)
        return logits
# class Decoder --------------------------------------------------------------


class TransformerTranslator(nn.Module):
    """인코더와 디코더를 하나로 묶는 전체 번역 모델입니다."""
    def __init__(self, vocab_size, embed_size, num_heads, num_layers):
        super().__init__()
        # 입력 문장을 의미 벡터로 압축하는 인코더를 생성함
        self.encoder = Encoder(vocab_size, embed_size, num_heads, num_layers)
        # 의미 벡터로부터 번역 문장을 생성하는 디코더를 생성함
        self.decoder = Decoder(vocab_size, embed_size, num_heads, num_layers)

    def forward(self, source_idx, decoder_input_idx):
        # 인코더가 입력 문장을 읽고 글자별 문맥 벡터 전체를 반환함
        encoder_outputs = self.encoder(source_idx)

        # 번역문 길이만큼 "미래 가림막"을 만듦 (아직 안 쓴 뒷글자를 못 보게 함)
        tgt_len = decoder_input_idx.size(1)
        # 삼각형 mask 생성 후, 입력과 같은 장치(CPU/GPU)에 올림
        tgt_mask = nn.Transformer.generate_square_subsequent_mask(tgt_len).to(source_idx.device)
        # 원문 출력 + 지금까지의 번역문 + 가림막을 디코더에 넣어 다음 글자 점수를 예측함
        logits = self.decoder(decoder_input_idx, encoder_outputs, tgt_mask)
        # 문자별 점수 텐서를 반환함
        return logits

