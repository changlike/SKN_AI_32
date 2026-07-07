"""PyCharm에서 바로 실행할 수 있는 BBC 기사 RNN 분류 프로젝트 진입점."""

from app.config import Config
from app.predict import load_artifacts, predict_text
from app.train import train_model


if __name__ == "__main__":
    # 프로젝트 전역 설정 객체를 생성한다.
    config = Config()

    # use_crawing=True 로 바꾸면 네이버 뉴스 실시간 크롤링으로 전환된다.
    # train_model(config, use_crawling=False)
    train_model(config, use_crawling=True)

    # 저장된 모델과 단어 사전, 라벨 사전을 다시 불러와 실제 서비스 예측 흐름을 확인한다.
    model, metadata = load_artifacts(config)

    # 새롭게 분류할 테스트 기사 문장을 준비한다.
    sample_news = "붉은악마 홍명보에 축구계 영원히 떠나라 적폐 사라질 때까지 투쟁"

    # 테스트 기사 문장을 모델에 입력하여 예측 카테고리를 얻는다.
    predicted_label = predict_text(sample_news, model, metadata, config)

    # 최종 예측 결과를 화면에 출력한다.
    print("\n새 기사:", sample_news)
    print("예측 카테고리:", predicted_label)
