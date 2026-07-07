# ====================================
# 자연어 텍스트 데이터 전처리 프로젝트 과제
# ====================================
# 데이터 출처: 뉴스 기사

import re
from collections import Counter

import torch
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from konlpy.tag import Okt

# 텍스트 수집
with open("text.txt", "r", encoding="utf-8") as f:
    text = f.read()

# 텍스트 정제
clean_text = re.sub(r"[^ㄱ-ㅎㅏ-ㅣ가-힣\s]", " ", text)
clean_text = re.sub(r"\s+", " ", clean_text).strip()

# 형태소 분석 (명사 추출)
nouns = Okt().nouns(clean_text)

# 불용어 제거 (불용어 사전 + 한 글자 단어 제거)
stopwords = {
    "이", "그", "저", "것", "수", "등", "및", "또", "더", "또한", "위해", "통해", "대해",
    "가운데", "가장", "다른", "다만", "때문", "만큼", "매번", "반면", "사실", "상황",
    "여기", "여유", "역시", "우리", "우선", "이번", "이상", "이제", "일제", "지금",
    "직전", "중이", "처음", "초반", "해도", "항상",
    "그었다", "안고", "상대로", "고작", "소위", "절대", "현재",
    "남아", "호의", "스포", "티비",
}
nouns = [word for word in nouns if word not in stopwords and len(word) > 1]

# 단어 빈도 계산 + 상위 20개 추출
word_freq = Counter(nouns)
top20 = word_freq.most_common(20)
print("상위 20개 단어:", top20)

# PyTorch Tensor 변환
words, counts = zip(*top20)
counts_tensor = torch.tensor(counts)

# 워드클라우드 생성
wordcloud = WordCloud(
    font_path="C:/Windows/Fonts/malgun.ttf",
    width=900,
    height=600,
    background_color="white",
).generate_from_frequencies(word_freq)

plt.rcParams["font.family"] = "Malgun Gothic"

# 워드클라우드 출력
plt.figure(figsize=(12, 8))
plt.imshow(wordcloud, interpolation="bilinear")
plt.axis("off")
plt.title("워드 클라우드")
plt.savefig("wordcloud.png", bbox_inches="tight")
plt.show()

# 상위 20개 단어 시각화
plt.figure(figsize=(12, 8))
plt.bar(words, counts_tensor.numpy())
plt.xticks(rotation=45, ha="right")
plt.title("상위 20개 단어 빈도")
plt.tight_layout()
plt.savefig("top20_words.png")
plt.show()

# 결과 분석 보고서 작성
report = f"""자연어 텍스트 데이터 전처리 결과 분석 보고서

1. 데이터 출처: 뉴스 기사 (text.txt)
2. 처리 과정: 정제 -> Okt 명사 추출 -> 불용어 제거({len(nouns)}개 단어) -> 빈도 계산 -> Tensor 변환 -> 시각화
3. 상위 20개 단어: {top20}
4. 가장 많이 등장한 단어는 '{top20[0][0]}'({top20[0][1]}회)이다.
"""
print(report)

with open("report.txt", "w", encoding="utf-8") as f:
    f.write(report)
