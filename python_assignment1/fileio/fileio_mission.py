# file.path: fileio\\fileio_mission.py
# module: fileio.fileio_mission

import pickle 

def emp_process():
    emp_dict = {}
    
    prompt = '''
     *** 직원 정보 관리 서비스 ***
        1. 새 직원정보 추가
        2. 직원정보 삭제
        3. 전체 출력
        4. 파일에 저장
        5. 파일로 부터 직원정보 읽어오기
        9. 서비스 끝내기    
    '''
    while True:
        print(prompt)
        num = int(input('원하는 번호 입력: '))

        if num == 1: 
            empid = input('사번:')
            empname = input('이름:')
            empno = input('주민번호:')
            email = input('이메일:')
            phone = input('전화번호:')
            salary = int(input('급여:'))
            job = input('직급:')
            dept = input('부서:')

            emp_dict[empid] = [empid, empname, empno, email, phone, salary, job, dept]

        elif num == 2:
            del_empid = input('삭제할 사번:')

            if del_empid in emp_dict:
                del emp_dict[del_empid]
                print(f'{del_empid} 번 사번의 직원 정보가 삭제되었습니다.')
            else:
                print("해당 사번은 존재하지 않습니다.")

        elif num == 3:
            for key in emp_dict:
                print(f'{key}:{emp_dict[key]}')
        
        elif num == 4:
            f = open('employees.dat', 'wb')
            pickle.dump(emp_dict, f)
            f.close()

            print(f'employees.dat 파일에 성공적으로 저장되었습니다.')

        elif num == 5:
            f = open('employees.dat', 'rb')
            emp_dict = pickle.load(f)
            f.close()

            print(emp_dict)

        elif num == 9: 
            print("직원 관리 프로그램을 종료합니다")
            break

        else:
            print("잘못된 번호입니다. 다시 입력해주세요.")




