//main.js
/*    
    자바스크립트 코드 external 방식 연습용 스크립트 파일임
*/
// (한줄 주석일 때 줄 앞에 // 두개 표시함)
/*
    여러 줄 주석일 때
*/

function testShow() {
    window.alert('main.js 에 작성된 testShow() 함수 실행됨');
}

function changeImage(){
    //document.getElementById('image1').src = '../images/d7.jpg';  //main.js 에서 images 까지의 상대경로 지정
    //main.js 를 가져다 사용한 html 문서 위치에서의 상대경로로 적용되어 에러 발생하게 됨
    //main.js 를 가져다 사용하는 웹문서들의 위치에 상관없이 경로를 지정하고자 한다면 절대경로를 사용해야 함
    // 절대경로는 슬러시(/)로 시작함
    // 웹프로젝트에서 웹서버 구동시 에플리케이션의 루트(Root)에서 시작하는 경로를 절대경로라고 함
    // 루트 폴더는 웹프로젝트 안의 web(또는 webapp) 임
    // vscode 에서는 절대경로 사용하려면, 폴더열기로 루트로 사용할 폴더를 열기하면 됨
    document.getElementById('image1').src = '/resources/images/d7.jpg'; 
}

function changeCSS(){
    //자바스크립트에서 html 태그의 속성(attribute)을 이용해서 태그의 정보를 변경할 수 있음
    //웹문서의 태그 정보를 조회해서, 해당 태그 정보를 저장해 놓고 이용할 수도 있음 => 변수를 사용함
    //자바스크립트에서 함수 안에서 변수 만들기 : var 변수명 = 저장할 정보;
    var element = document.getElementById('demo3');
    element.style.color = '#ff00cc';
    element.style.border = '3px double black';
    element.style.fontSize = '14pt';
    element.style.backgroundColor = 'yellow';
}

function calculate(){
    // input 에 기록된 값을 읽어와서, 변수공간에 저장 처리
    var num1 = document.getElementById('num1').value;
    var num2 = document.getElementById('num2').value;

    //자바스크립트 내장함수 : typeof(변수명 | 값 | 계산식) => 자료형 확인용 함수임
    console.log('num1 : ' + typeof(num1) + '\n');  //string (문자열 : 문자나열값)
    console.log('num2 : ' + typeof(num2) + '\n');  //string (문자는 컴퓨터에서 계산할 수 없는 값을 의미함)
    //계산하려면 string 을 숫자로 바꿔야 함 : 파싱(parsing) 이라고 함
    //자바스크립트 내장함수 : Number(문자열숫자) => 숫자로 파싱됨
    var result = Number(num1) + Number(num2);

    //더하기한 계산 결과를 input(id : result)에 출력 처리
    document.getElementById('result').value = result;
    document.getElementById('demo4').innerHTML = '결과 확인<br>' + result;
}

//data type(값의 종류) : 프로그래밍 언어마다 약간씩 차이가 있음
//컴파일 프로그램 언어 (C, C++, java, c#.net 등) : 자료형을 코드 구문에서 명시함
//인터프리터 언어 (자바스크립트, 파이썬 등) : 코드 구문에 자료형 명시 안 함 => 사용시 값의 종류를 구분은 함
//자바스크립트에서는 값의 data type 이 뭔지 확인은 할 수 있음 => typeof 함수 사용함
// 계산 못 하는 데이터 - 문자하나, 문자나열값(문자열) : string
// 계산할 수 있는 데이터 - 숫자(정수, 실수) : number
// 논리값(참 true, 거짓 false) :  boolean

function checkType(){
    console.log(typeof('apple') + '\n'
            + typeof('A') + '\n'
            + typeof(123) + '\n'
            + typeof(34.5) + '\n'
            + typeof('7' + 12) + '\n'
            + typeof(34 + '5') + '\n'
            + typeof(3 == 4) + '\n'
            + typeof(val) + '\n');
}