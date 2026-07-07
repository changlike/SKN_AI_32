# test1.py
# 한글 형태소 분석기 사용 테스트 1

# Hananum : KAIST  말뭉치를 이용해 생성된 사전 분석기
from konlpy.tag import Hannanum

hananum = Hannanum()

# 제공 메소드: 레퍼런스.메소드명() 사용
# analyze: 구(parse) 분석
# morphs(): 형태소 분석
# nouns(): 명사만 분석
# pos(): 형태소 분석 + 태깅

# 사용
print('Hananum 분석기 이용 -----------------')
text = u'길동 마트의 흑마늘 양념 치킨이 논란이 되고 있다.'
print(hananum.analyze(text))
print(hananum.morphs(text))
print(hananum.nouns(text))
print(hananum.pos(text))

# KKma (꼬꼬마): 세종 말뭉치를 이용해 생성된 사전 분석기(서울대에서 만듦)
from konlpy.tag import Kkma

kkma = Kkma()

# 메소드 정리
# setences(): 문장 분석
# morphs(): 형태소 분석
# nouns(): 명사만 분석
# pos(): 형태소 분석 + 태깅

from konlpy.tag import Komoran

kom = Komoran()

print('Komoran 분석기 이용 ------------------')
print(kom.morphs(text))
print(kom.nouns(text))
print(kom.pos(text))

# Twitter(Okt) : 오픈소스 한글 형태소 분석기
from konlpy.tag import Okt

okt = Okt()

print('Okt 분석기 이용 ------------------')
print(okt.phrases(text))
print(okt.morphs(text))
print(okt.nouns(text))
print(okt.pos(text))

# stem: 각 단어에서 어간 추출 처리 매개변수
print('Okt method: stem parameter using ---------------')
print(okt.morphs(text, stem=True))
