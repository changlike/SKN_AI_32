# file.path: loop\\while_mission.py
# module: loop.while_mission

def sungjuk_process():
    sungjuk_list = [[12, '홍길동', 98], [15, '김유신', 87], [23, '황지니', 45]]

    prompt = ''' 
        *** 원하는 메뉴 번호를 선택하세요. ***   
            1. 추가
            2. 삭제
            3. 출력
            4. 끝내기
    '''
    
    while True:
        print(prompt)
        num = int(input('원하는 메뉴 번호 입력:'))

        if num == 1:
            sno = int(input('번호: '))
            sname = input('이름: ')
            score = int(input('점수: '))
            
            sungjuk_list.append([sno, sname, score])
            print("새로운 학생정보가 추가되었습니다.")

        elif num == 2:
            print(f'현재 저장된 아이템의 갯수는 {len(sungjuk_list)}개 입니다.')
            del_lst = int(input('제거할 아이템의 순번:'))
            
            if 0 <= del_lst < len(sungjuk_list):
                sungjuk_list.pop(del_lst)
                print(f'{del_lst}번 위치의 아이템이 제거되었습니다.\n 현재 저장된 아이템의 갯수는 {len(sungjuk_list)}개 입니다.')
            else: 
                print("순번이 잘못 입력되었습니다. 확인하고 다시 입력하세요.")

        elif num == 3:
            i = 0 
            while i < len(sungjuk_list):
                print(f'{i} : {sungjuk_list[i]}')
                i += 1

        elif num == 4:
            print("성적관리 프로그램이 종료되었습니다.")
            break 

        else:
            print("잘못된 입력입니다.")

    







