# app/data.py
"""네이버 뉴스 샘플 데이터(방법1) + 크롤링 함수(방법2)."""

from __future__ import annotations

from typing import List, Tuple

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# ------------------- 방법 1: 직접 복사한 샘플 데이터 -------------------------------
SAMPLE_DATA: List[Tuple[str, str]] = [
    ("붉은악마 홍명보에 축구계 영원히 떠나라 적폐 사라질 때까지 투쟁", "sport"),
    ("역대급 꿀조에서 조 3위 탈락 눈물의 사퇴 기자회견 아르헨 명장 우루과이서 불명예 퇴출 아무런 성과 없이 떠난다", "sport"),
    ("김병지, 돌연 해명! 역할 최선 다해...'월드컵 참사 후폭풍' 협회 부회장직까지 의심받자, 결국 직접 입 열었다", "sport"),
    ("홍명보 감독 자진 사퇴→박항서 단장도 고개 숙여 사과…뼈를 깎는 반성과 성찰로 미래 준비하겠다", "sport"),
    ("붉은악마 진심을 바치고 바보 됐다...축구 적폐 사라질 때까지 투쟁 입장문 공개", "sport"),
    ("3년 전엔 적자였는데…엔비디아·구글 빼면 美서 제일 돈 잘 버는 이 기업", "business"),
    ("모처럼 웃음꽃 핀 코스닥…정책자금 호재에 8%대 급등 마감(종합)", "business"),
    ("이재용 반도체 투자, 광주 후보지…로봇은 구미·배터리는 울산 투자", "business"),
    ("삼성·SK, 최소 2500조 이상 투자…AI·반도체 초격차 완성(종합)", "business"),
    ("반도체뿐 아니다 이재용號 삼성, 로봇·바이오·배터리 전국서 '전방위 투자", "business"),
    ("李 용인·평택 반도체 이미 한계…서남권 대규모 신규 투자", "politics"),
    ("진종오 축구협회 전면 해체해야…여야, 홍명보호 참사 질타", "politics"),
    ("민주당 의원들 호남 땅 공개하라…반도체 특혜 공방, 부동산으로 번지나", "politics"),
    ("홍명보호 32강 진출 실패…정치권 한국 축구 대수술 절실", "politics"),
    ("이 대통령 반도체·AI·데이터센터 삼각축으로 초격차 강국 도약", "politics"),
    ("애플 첫 터치스크린 맥북 프로, M5프로·맥스 탑재", "tech"),
    ("인텔, 자체 개발 에이전틱 AI 플랫폼 슈퍼클로 베타 공개", "tech"),
    ("최태원 AI데이터센터 1천조·반도체 공급 확장 1천100조 투자", "tech"),
    ("배경훈 2029년까지 AIDC 550조 투자…2035년엔 1천조 넘는다", "tech"),
    ("춤추는 로봇 넘는다…휴머노이드 국가대표 경쟁", "tech"),
    ("안정환, '되지도 않는 것들이' 발언 해명.. 홍명보 나가, 눈치 본 거 아냐", "entertainment"),
    ("선수들은 죄가 없다…전현무 한마디에 이영표 감독 비중 50%", "entertainment"),
    ("김무열♥ 윤승아, 새벽 4시반에 80만원 쇼핑 폭주 잠 안와서 결국..", "entertainment"),
    ("안정환 가족은 건드리지 말라", "entertainment"),
    ("김병현 홍명보에 예의 갖춰야 소신 발언...김영광에 일침 가했다가 갑론을박", "entertainment"),
]


def load_sample_data() -> Tuple[List[str], List[str]]:
    """내장 샘플 데이터를 기사 문장 목록과 라벨 목록으로 분리해서 반환한다."""
    texts = [text for text, _ in SAMPLE_DATA]
    labels = [label for _, label in SAMPLE_DATA]
    return texts, labels


# -------------- 방법 2: naver 뉴스 크롤링 함수 --------------------
headers = {"User-Agent": "Mozilla/5.0"}  # 네이버 서버가 봇으로 차단하지 않도록 브라우저처럼 요청한다.


def _fetch_titles(url: str, label: str) -> List[Tuple[str, str]]:
    """requests로 정적 HTML에서 기사 제목을 수집한다 (tech, business, politics용)."""
    resp = requests.get(url, headers=headers, timeout=5)
    soup = BeautifulSoup(resp.text, "html.parser")
    titles = (
        soup.select("a.news_tit") or
        soup.select("a.sa_text_title") or
        soup.select("a.api_txt_lines")
    )
    print(f"[{label}] 수집된 제목 수: {len(titles)}")
    return [(tag.get_text(strip=True), label) for tag in titles if tag.get_text(strip=True)]


def _fetch_titles_selenium(url: str, label: str) -> List[Tuple[str, str]]:
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--user-agent=Mozilla/5.0")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager(driver_version="149").install()),
        options=options
    )
    try:
        driver.get(url)
        import time
        time.sleep(3)  # JS 렌더링 완전히 끝날 때까지 3초 대기한다.

        # a태그와 span, em 태그 모두 수집해서 제목 후보를 넓힌다.
        elements = (
                driver.find_elements(By.TAG_NAME, "a") +
                driver.find_elements(By.TAG_NAME, "em") +
                driver.find_elements(By.TAG_NAME, "span")
        )
        seen = set()
        titles = []
        for el in elements:
            text = el.text.strip()
            if 10 < len(text) < 80 and text not in seen:  # 길이 조건 80자로 완화, 중복 제거
                seen.add(text)
                titles.append((text, label))

        print(f"[{label}] 수집된 제목 수: {len(titles)}")
        return titles
    except Exception as e:
        print(f"[{label}] Selenium 수집 실패: {e}")
        return []
    finally:
        driver.quit()

def get_news_tech() -> List[Tuple[str, str]]:
    """네이버 뉴스 IT/과학 카테고리 제목을 수집한다."""
    return _fetch_titles("https://news.naver.com/section/105", "tech")


def get_news_sport() -> List[Tuple[str, str]]:
    """네이버 스포츠 Selenium 크롤링 (JS 렌더링 페이지)."""
    return _fetch_titles_selenium("https://sports.naver.com", "sport")


def get_news_entertainment() -> List[Tuple[str, str]]:
    """네이버 연예 Selenium 크롤링 (JS 렌더링 페이지)."""
    return _fetch_titles_selenium("https://entertain.naver.com", "entertainment")


def get_news_business() -> List[Tuple[str, str]]:
    """네이버 뉴스 경제 카테고리 제목을 수집한다."""
    return _fetch_titles("https://news.naver.com/section/101", "business")


def get_news_politics() -> List[Tuple[str, str]]:
    """네이버 뉴스 정치 카테고리 제목을 수집한다."""
    return _fetch_titles("https://news.naver.com/section/100", "politics")


def load_crawled_data() -> Tuple[List[str], List[str]]:
    """방법2: 5개 카테고리를 크롤링해서 텍스트, 라벨 목록으로 반환한다."""
    all_data: List[Tuple[str, str]] = []
    for fetcher in [get_news_tech, get_news_sport, get_news_entertainment,
                    get_news_business, get_news_politics]:
        try:
            all_data.extend(fetcher())
        except Exception as e:
            print(f"[크롤링 실패] {fetcher.__name__}: {e}")  # 실패해도 나머지 카테고리는 계속 수집한다.

    texts = [text for text, _ in all_data]
    labels = [label for _, label in all_data]
    return texts, labels