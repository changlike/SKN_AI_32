# main.py 

import loop.while_mission as lw
import fileio.fileio_mission as fi

def menu():
    prompt = '''
    *** 파이썬 과제 1 ***
	1. while 실습문제
	2. fileio 실습문제
	9. 과제 실행 테스트 끝내기
    '''

    while True:
        print(prompt)
        num = int(input('원하는 메뉴 번호 입력 : '))

        if num == 1:
            lw.sungjuk_process()

        if num == 2:
            fi.emp_process()

        if num == 9:
            print("과제 실행 테스트를 끝냅니다.")
            break

if __name__ == '__main__':
    menu()
    print("프로그램을 종료합니다.")


