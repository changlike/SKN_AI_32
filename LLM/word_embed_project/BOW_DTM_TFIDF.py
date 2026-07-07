# BOW_DTM_TFIDF.py
'''
BOW(Bag of Words)
: 단어의 순서는 고려하지 않고, 단어가 몇번 등장했는지에  집중하는 텍스트 수치화 방법임

DTM(Document-Term Matrix)
: 여러 문서의 BOW 를 하나의 행렬로 모은 것

TF-IDF
: TF는 특정 문서 안에서 단어가 얼마나 자주 등장하는지를 나타냄
- IDF는 전체 문서에서 흔한 단어의 가중치는 낮추고, 흔하지 않은 단어의 가중치를 높임
'''
import sys
import subprocess
from math import log

try:
    from sklearn.feature_extraction.text import CountVectorizer
except ModuleNotFoundError as e:
    raise ModuleNotFoundError("scikit-learn not installed. 터미널에서 pip install scikit-learn 직접 설치하세요.") from e

try:
    from konlpy.tag import Okt
    okt = Okt()
    KONLPY_AVAILABLE = True  # KONLPY 사용 가능 상태
except Exception as e:
    okt = None
    KONLPY_AVAILABLE = False
    KONLPY_ERROR = e # 오류 원인을 나중에 출력하도록 변수에 보관함

try:
    import nltk
    from nltk.corpus import stopwords
    NLTK_AVAILABLE = True
except ModuleNotFoundError as e:
    nltk = None
    stopwords = None
    NLTK_AVAILABLE = False

# 공통 출력 함수 정의 ============================
def print_section(title): # 실습 단계별 제목을 보기좋게 출력하기 위한 함수
    """콘솔에서 실습 구간을 구분하기 위한 제목 출력 함수입니다."""
    print('\n' + '=' * 80)
    print(title)
    print('=' * 80)

# BOW 직접 구현: 한국어 형태소 분석 기반 Bag Of Words 생성
print_section("1. BOW 구현: 한국어 문장을 단어 빈도 벡터로 변환")

if not KONLPY_AVAILABLE:  # konlpy 사용이 불가능하다면
    print('[안내] konlpy.Okt 실행에 실패했습니다.')
    print('[대체 실행] 현재 코드는 공백 기반 토큰화를 사용하여 계속 실행합니다.')

def tokenize_korean(document): # 한국어 문장을 토큰 리스트로 변환하는 함수
    """Okt가 가능하면 형태소 분석을 사용하고, 불가능하면 공백 기준으로 토큰화합니다."""
    cleaned_document = document.replace(".", '') # 마침표 제거(불필요한 기호 제거: 정졔)
    cleaned_document = cleaned_document.replace(",", " ") # 쉼표 제거
    if KONLPY_AVAILABLE:
        return okt.morphs(cleaned_document) # 형태소 단위로 분리해서 리턴
    return cleaned_document.split() # 공백 기준으로 단어들을 나눔(토큰화)

def build_bag_of_words(document): # 하나의 문서에서 BOW 사전과 빈도 벡터를 만드는 함수
    """전달받은 문서에서 단어 인덱스 사전과 단어 빈도 벡터를 생성하는 함수입니다."""
    tokenized_document = tokenize_korean(document) # 문장을 토큰 단위로 나눈 결과 받음
    word_to_index = {} # 단어별 고유 인덱스를 저장할 빈 딕셔너리 생성
    bow = [] # 각 단어 인덱스 위치에 등장 횟수를 저장할 빈 리스트 생성
    for word in tokenized_document: # 토큰화된 단어를 하나씩 처리
        if word not in word_to_index: # 현재 사전에 등록되지 않은 단어라면
            word_to_index[word] = len(word_to_index) # word: index로 저장
            bow.append(1) # 새 단어 등록에 대한 빈도 1을 추가 (index 순번을 맞춰서 저장함)
        else: # 현재 단어가 사전에 등록되어 있다면
            index = word_to_index[word] # 기존 등록된 단어의 순번을 조회함
            bow[index] += 1  # 해당 인덱스 위치의 빈도를 1증가시킴
    return word_to_index, bow  # 단어 인덱스 사전과 빈도 벡터 리턴함

# bow 사용 테스트 ------------------------------------------------------------
doc1 = "파이썬을 이용한 텍스트 빈도수 카운트 실습을 진행합니다."
vocab, bow = build_bag_of_words(doc1)  # 예제 문장을 BOE 사전과 빈도 벡터로 변환함
print("입력 문장: ", doc1)  # 원본 텍스트 출력
print("Vocabulary: ", vocab) # 단어별 인덱스 사전 출력
print("Bag Of Words Vector:", bow) # 단어 등장 빈도 벡터 출력


# ==================================================================
# 2 . CountVectorizer를 이용한 BOW 생성
# ==================================================================

print_section("2. CountVectorizer를 이용한 BOW 생성")

corpus = ["you know I want your love. I love you."]
vec = CountVectorizer()
bow_matrix = vec.fit_transform(corpus).toarray()
# 코퍼스를 학습하고, 단어 빈도 행렬을 배열로 변환함
print("입력 코퍼스: " , corpus)
print("bag of words matrix: ")
print(bow_matrix) # 문서-단어 빈도 행렬 출력
print("Vocabulary: :")
print(vec.vocabulary_)  # CountVectorize가 만든 단어 인덱스 사전 출력

# 3. 불용어 제거 =======================================================
print_section("3. 사용자가 직접 정의한 불용어 제거")

text = ["Family is not an important thing. It's everything."]
custom_stop_words = ["the", "a", "an", "is", "not"] # 직접 작성한 불용어 리스트
vect_custom = CountVectorizer(stop_words=custom_stop_words)  # 불용어 제거
custom_matrix = vect_custom.fit_transform(text).toarray()
print("입력 문장: ", text)
print("직접 정의한 불용어: ", custom_stop_words)
print("bow vector: ", custom_matrix)
print("Vocabulary: ")
print(vect_custom.vocabulary_)

# nltk가 제공하는 불용어 사전을 이용해서 불용어 제거할 수도 있음
# CountVectorizer에서 제공하는 영어 기본 불용어 사용 제거할 수도 있음

# 3. 워드 임베딩 =======================================================
print_section("3. DTM과 TF-IDF 실습")

docs = {
    "배우고 싶은 자연어",   # 첫번째 문서
    "딥러닝 머신러닝 배우고 싶은 강화학습", # 두번째 문서
    "자연어 처리 좋아요", # 세번째 문서
    "배우고 싶은 딥러닝", # 네번째 문서
}

vocab = sorted(set(word for doc in docs for word in doc.split()))
N = len(vocab) # 단어 갯수 저장
print("문서 목록")
for idx, doc in enumerate(docs, start=1):  # enumerate -> 목록을 만들기
    print(f'문서{idx} : {doc}')  # 번호 : 문서 출력
print("Vocabulary:", vocab)
print("문서개수 N: ", N) # 전체 문서 갯수