# path: ./app/core/hf/pipelines.py
'''
Hugging Face 파이프라인을 서버 시작시 1번만 로딩하기 위한 모듈임
  => 요청마다 모델을 로딩하면 요청 처리 속도가 매우 느림
  => 서버가 구동될 때 모델을 미리 메모리에 올려두고, 요청시 로딩되어 있는 모델을 사용하게 함
pipeline 은 전처리(토크나이징) -> 모델 추론 -> 후처리를 묶어주는 API 임

* API(Application Programming Interface) :
  프로그램과 프로그램이 대화하는 공식 규칙(약속)
  => 프로그램은 API를 통해 다른 프로그램의 기능을 사용함
  예>
  날씨 앱 --> 기상청 API 호출 : 기상청이 제공하는 날씨 정보 처리하는 프로그램을 연결 사용함
  로그인 --> 인증 서버 API 호출
  쇼핑몰 --> 결제 API 호출
  AI 서비스 --> OpenAI API 호출

* API 동작 구조:
  클라이언트 -> 요청 (Request) -> 서버 API (요청을 처리하고 결과 반환) -> 응답(Response) -> 클라이언트
'''

from transformers import pipeline, Pipeline
from app.core.config import settings

class HFPipelineManager:
    """
    모델 파이프라인들을 보관/관리하는 매니저 클래스
    """
    def __init__(self):
        """
        로딩 상태 정보를 저장 (정상 상태인지 확인용)
        """
        self.info = {
            "text-classification": {"model": settings.CLS_MODEL, "loaded": False},
            "summarization": {"model": settings.SUM_MODEL, "loaded": False},
            "translation": {"model": settings.TRANS_MODEL, "loaded": False},
        }

        # 실제 pipeline 객체
        self.cls_pipe = None
        self.sum_pipe = None
        self.trans_pipe = None
    # def_init()

    def load_all(self):
        """
        서버 시작 시 호출해서 파이프라인을 미리 로딩함
        """
        # 1. Text Classification 파이프라인 로딩
        # task="text-classification" : 감성분석/문장분류 등을 의미하는 sequence classification 에 해당됨을 지정함
        self.cls_pipe = pipeline(
            task="text-classification",
            model=settings.CLS_MODEL,
            device=settings.DEVICE,
        )
        self.info["text-classification"]["loaded"] = True

        # 2. Summarization 파이프라인 로딩
        self.sum_pipe = pipeline(
            task="summarization",
            model=settings.SUM_MODEL,
            device=settings.DEVICE,
        )
        self.info["summarization"]["loaded"] = True

        # 3. Translation 파이프라인 로딩
        # 번역은 task 이름이 'translation' 또는 'translation_xx_to_yy' 형태로도 사용할 수 있음
        self.trans_pipe = pipeline(
            task="translation",
            model=settings.TRANS_MODEL,
            device=settings.DEVICE,
        )
        self.info["translation"]["loaded"] = True

        return self.info
    # def end ------------------------------

    def classify(self, text: str):
        """
        텍스트 분류 실행
        - pipeline 실행 결과는 보통 [{'label': 'POSITIVE', 'score':0.9999}] 형태
        """
        return self.cls_pipe(text)
    # def end -----------------------------

    def translate(self, text: str):
        """
        번역 실행 (NLLB 기준)
        - 결과는 [{'translation_text': '번역결과문자열'}]
        """
        return self.trans_pipe(
            text,
            src_lang="eng_Latn",   # 입력언어: 영어
            tgt_lang="kor_Hang",   # 출력언어: 한국어
        )
    # def end ----------------------------------------

    def summarize(self, text: str, max_length: int, min_length: int):
        """
        요약 실행
        - 결과는 [{'summary_text': '요약내용 문자열'}]
        """

        return self.sum_pipe(
            text,
            max_length=max_length,
            min_lenth=min_length,
            truncation=True     # 입력이 너무 클 경우 자동 절단
        )
    # def end --------------------------------------

# class end ----------------------------------------------------------------

# 모듈 전역변수로 선언 (싱글톤)
hf_manager = HFPipelineManager()







