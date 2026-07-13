'''
문제 1 — 청킹 함수 직접 구현
chunk_text(text, size=500, overlap=50) 함수를 직접 작성하세요.

글자 수 기준으로 자르되 지정한 overlap만큼 겹치게 합니다.
사용 파일: data/docs/직원핸드북.pdf (텍스트 추출 후 입력)
기대 결과: 청크 개수, 그리고 첫 청크와 둘째 청크의 겹치는 50자가 동일함을 검증하면 성공
'''

from pypdf import PdfReader

def chunk_text(text, size=500, overlap=50):
    """
    긴 텍스트를 지정한 크기로 자르되,
    앞뒤 chunk가 overlap 글자만큼 겹치도록 나누는 함수
    """
    chunks = []   # 완성된 청크들을 담을 리스트
    start = 0      # 현재 자르기 시작할 위치 (매 반복마다 갱신)

    while start < len(text):
        # 현재 위치부터 size만큼 잘라서 청크 하나 생성
        chunk = text[start:start+size]
        chunks.append(chunk)

        # 다음 시작 위치 = 이번 시작점 + size - overlap
        # (overlap만큼 뒤로 물러서서 겹치게 만드는 핵심 로직)
        start = start + size - overlap

    return chunks

# PDF에서 텍스트 추출
reader = PdfReader("../data/docs/직원핸드북.pdf")
full_text = ""
for page in reader.pages:
    full_text += page.extract_text()

# 청킹 실행
chunks = chunk_text(full_text, size=500, overlap=50)

print('-'*10, '문제 1', '-'*10)
print(f"총 청크 개수: {len(chunks)}")
print(f"첫 청크 마지막 50자: {chunks[0][-50:]}")
print(f"둘재 청크 처음 50자: {chunks[1][:50]}")
print(f"겹침 검증: {chunks[0][-50:] == chunks[1][:50]}")

'''
문제 2 — 청크 크기 비교
chunk_size를 200/500/1000으로 바꿔가며 청크 개수와 평균 길이를 표로 출력하세요.

사용 파일: data/docs/환불교환정책.pdf
기대 결과: size가 커질수록 청크 수가 줄어드는 경향을 확인하고, "조항 단위 검색에 적합한 크기"를 한 줄로 결론내면 성공.
'''

# size별로 비교
sizes = [200, 500, 1000]

# 환불교환정책.pdf로 바꾸기
reader2 = PdfReader("../data/docs/환불교환정책.pdf")
full_text2 = ""
for page in reader2.pages:
    full_text2 += page.extract_text()

print('\t')
print('-'*10, '문제 2', '-'*10)

print(f"{'size':<10}{'청크 수':<10}{'평균 길이':<10}")
print("-" * 30)

for size in sizes:
    chunks = chunk_text(full_text2, size=size, overlap=50)
    개수 = len(chunks)
    평균_길이 = sum(len(c) for c in chunks) / len(chunks)

    print(f"{size:<10}{개수:<10}{평균_길이:<10.1f}")