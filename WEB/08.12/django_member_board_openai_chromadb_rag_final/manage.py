#!/usr/bin/env python
"""Django 관리 명령을 실행하기 위한 프로젝트 진입 파일입니다."""
# 운영체제 환경변수를 다루기 위해 os 모듈을 가져옵니다.
import os
# 명령행 인자를 Django에 전달하기 위해 sys 모듈을 가져옵니다.
import sys


def main():
    """settings 모듈을 지정한 뒤 Django 관리 명령을 실행합니다."""
    # DJANGO_SETTINGS_MODULE이 별도로 지정되지 않았다면 프로젝트 설정 파일을 기본값으로 사용합니다.
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    try:
        # Django의 manage.py 명령 처리 함수를 필요한 시점에 가져옵니다.
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        # Django가 설치되지 않았을 때 원인을 알기 쉬운 메시지로 다시 발생시킵니다.
        raise ImportError("Django가 설치되지 않았습니다. pip install -r requirements.txt 를 실행하세요.") from exc
    # python manage.py 뒤에 입력한 migrate, runserver 등의 명령을 Django에 전달합니다.
    execute_from_command_line(sys.argv)


# 이 파일이 직접 실행될 때만 main() 함수를 호출합니다.
if __name__ == "__main__":
    main()
