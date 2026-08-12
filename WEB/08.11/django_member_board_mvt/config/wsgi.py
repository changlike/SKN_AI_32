"""WSGI 서버가 Django 애플리케이션을 구동할 때 사용하는 설정 파일입니다."""
# 환경변수 설정을 위해 os 모듈을 가져옵니다.
import os
# WSGI application 객체를 생성하는 Django 함수를 가져옵니다.
from django.core.wsgi import get_wsgi_application
# 기본 settings 모듈을 지정합니다.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
# 웹 서버가 호출할 WSGI 애플리케이션 객체를 생성합니다.
application = get_wsgi_application()
