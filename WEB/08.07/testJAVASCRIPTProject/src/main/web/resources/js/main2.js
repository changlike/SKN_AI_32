/*
    main2.js   
*/

// 자바스크립트에서 제공되는 다이얼로그 확인용 함수 (window 내장 객체가 제공함) 작성
function showAlert(){
    window.alert('출력 메세지와 확인 버튼 제공하는 알림창임');
}

function showConfirm(){
    var returnValue = window.confirm('찬성하면 확인, 반대하면 취소를 선택하세요.');
    document.getElementById('result').innerHTML = '리턴값 확인 : ' + returnValue + ', 자료형 : ' + typeof(returnValue);
}

function showPrompt(){
    var inputValue = window.prompt('주소를 입력하세요.');
    document.getElementById('result').innerHTML = '입력된 주소 확인 : ' + inputValue;
}

// input 을 통해서 값을 입력받는 방법 확인용 함수
function testInput(){
    //input 태그에 기록된 값을 value 속성으로 가지고 와서, 변수에 저장 처리함
    var userName = document.getElementById('username').value;
    //window.alert('input 에 기록된 이름 : ' + userName);
    alert('input 에 기록된 이름 : ' + userName);
    // 자바스크립트 내장 객체중 window 객체가 최상위 객체임. window 가 제공하는 메소드나 속성은 window. 을 생략해도 됨
}

// input 입력 연습용 함수 : 간단 계산기 기능 처리용
// 함수는 매개변수(parameter)가 없는 함수 : function 함수명() <- 괄호 안이 비어있는 경우
// => 사용시 : on이벤트명="함수명();" <- 빈 괄호로 사용함
// 매개변수가 있는 함수 : function 함수명(매개변수명, 변수, 변수, ......) <- 괄호 안에 변수가 1개 이상 있는 경우
// => 사용시 : on이벤트명="함수명(전달값, ......);"  <- 매개변수 갯수에 맞춰서 매개변수에게 전달할 값을 괄호 안에 반드시 기입해야 함
function calculator2(op){
    // input 으로 입력되는 모든 종류(type)의 값은 모두 string(문자)임
    // 15 라고 입력하면 '15' 로 전달받게 됨 => 계산에 사용 못 하는 값임
    // 문자를 숫자로 바꾸는 파싱 함수 제공함 : Number('숫자문자') => 숫자로 바꿈
    var n1 = Number(document.getElementById('n1').value);
    var n2 = Number(document.getElementById('n2').value);

    var result;

    /*
    함수(기능) 안 코드 작성 순서 : 
        1. 필요한 변수 선언과 값 기록
        2. 추가로 필요한 값 입력받아서 변수에 기록 저장
        3. 제어문 사용 (원하는 작동이 되게 제어 처리가 목적, 연산자와 함께 사용됨)
        4. 출력 처리 또는 함수 실행 위치로 결과 반환 처리

        제어문 : 조건문, 반복문, 분기문로 구분됨
        조건문 : 주로 관계(비교) 연산자와 논리 연산자를 이용해서 제어 처리함
            if 문, switch 문

        switch 문은 선택문이라고도 함 (선택을 위한 구문)
        switch(선택을 위한 변수 또는 계산식){
            case 값제시:  제시한 값이 맞으면 실행할 구문; break;
            //제시값이 아니면 아래의 case 로 내려가는 구조임
            case 값제시:  
            ......
            default:  위에 제시된 값이 모두 아닐 때 실행할 구문;  // 생략할 수 있음
        }
    */
    switch(op){  //op 변수가 가진 값이 뭐냐? (주의 : true | false 결과나 논리값은 사용 못 함)
        case '+': result = n1 + n2; break;  //break : switch 문을 종료하는 구문임
        case '-': result = n1 - n2; break;  // case 에는 값만 제시할 수 있음, 조건식 사용 못 함
        case '*': result = n1 * n2; break;
        case '/': result = n1 / n2; break;
        case '%': result = n1 % n2; break;
    }

    document.getElementById('calc').innerHTML = n1 + ' ' + op + ' ' + n2 + ' = ' + result;
}