// 화면 요소를 조회합니다.
const q=document.getElementById('question'), mode=document.getElementById('mode'), topK=document.getElementById('topK'), send=document.getElementById('send'), answer=document.getElementById('answer'), sources=document.getElementById('sources'), evalBtn=document.getElementById('evalBtn'), evaluation=document.getElementById('evaluation');
// 질문 버튼 이벤트를 연결합니다.
send.addEventListener('click',async()=>{
  // 공백을 제거한 질문을 읽습니다.
  const question=q.value.trim();
  // 빈 질문을 차단합니다.
  if(!question){answer.textContent='질문을 입력하십시오.';return;}
  // 선택 모드에 맞는 API를 결정합니다.
  const endpoint=mode.value==='rag'?'/api/rag/chat':'/api/chat';
  // 중복 클릭을 막습니다.
  send.disabled=true;
  // 진행 상태를 표시합니다.
  answer.textContent='생성 중...';
  try{
    // FastAPI에 JSON 요청을 보냅니다.
    const response=await fetch(endpoint,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question,top_k:Number(topK.value)})});
    // JSON 응답을 읽습니다.
    const data=await response.json();
    // 실패 상태이면 예외를 발생시킵니다.
    if(!response.ok)throw new Error(data.detail||`HTTP ${response.status}`);
    // 모델 답변을 표시합니다.
    answer.textContent=`[${data.backend}]

${data.answer}`;
    // 검색 근거를 안전한 텍스트 노드로 표시합니다.
    sources.replaceChildren(...(data.sources||[]).map((s,i)=>{const a=document.createElement('article');const h=document.createElement('strong');h.textContent=`근거 ${i+1}: ${s.source} (${s.score.toFixed(4)})`;const p=document.createElement('p');p.textContent=s.text;a.append(h,p);return a;}));
  }catch(error){
    // 오류 메시지를 표시합니다.
    answer.textContent=`오류: ${error.message}`;
  }finally{
    // 버튼을 다시 활성화합니다.
    send.disabled=false;
  }
});
// 평가 결과 조회 이벤트를 연결합니다.
evalBtn.addEventListener('click',async()=>{
  // 평가 API를 호출합니다.
  const response=await fetch('/api/evaluation');
  // JSON을 읽습니다.
  const data=await response.json();
  // 결과 또는 오류를 표시합니다.
  evaluation.textContent=response.ok?JSON.stringify(data,null,2):(data.detail||'조회 실패');
});
