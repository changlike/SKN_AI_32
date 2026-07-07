const resultBox = document.getElementById('resultBox');
const statusCard = document.getElementById('statusCard');

function value(id) {
  return document.getElementById(id).value;
}

function numberValue(id) {
  return Number(document.getElementById(id).value);
}

function showLoading(title) {
  resultBox.textContent = `${title}\n\n요청 처리 중입니다...`;
}

function showResult(title, data) {
  resultBox.textContent = `${title}\n\n${JSON.stringify(data, null, 2)}`;
}

function showError(title, error) {
  resultBox.textContent = `${title}\n\n오류가 발생했습니다.\n${error.message || error}`;
}

async function postJson(url, body) {
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || JSON.stringify(data));
  }

  return data;
}

async function checkHealth() {
  try {
    const response = await fetch('/api/system/health');
    const data = await response.json();
    statusCard.innerHTML = `<strong>상태:</strong> ${data.status || '확인 완료'} / ${data.message || '서버가 실행 중입니다.'}`;
  } catch (error) {
    statusCard.innerHTML = `<strong>상태:</strong> 서버 상태 확인 실패 - ${error.message}`;
  }
}

document.getElementById('healthBtn').addEventListener('click', checkHealth);
window.addEventListener('load', checkHealth);

async function callBasic() {
  const title = 'Gemini 기본 호출 결과';
  showLoading(title);
  try {
    const data = await postJson('/api/llm/gemini/basic', {
      prompt: value('basicPrompt'),
      temperature: numberValue('basicTemperature'),
      max_output_tokens: numberValue('basicMaxTokens'),
    });
    showResult(title, data);
  } catch (error) {
    showError(title, error);
  }
}

async function callRole() {
  const title = '시스템 지시 역할 테스트 결과';
  showLoading(title);
  try {
    const data = await postJson('/api/llm/gemini/role', {
      system_instruction: value('roleSystem'),
      user_message: value('roleUser'),
      temperature: numberValue('roleTemperature'),
      max_output_tokens: numberValue('roleMaxTokens'),
    });
    showResult(title, data);
  } catch (error) {
    showError(title, error);
  }
}

async function callDiversity() {
  const title = 'Temperature 다양성 테스트 결과';
  showLoading(title);
  try {
    const data = await postJson('/api/llm/gemini/diversity', {
      prompt: value('diversityPrompt'),
      temperature: numberValue('diversityTemperature'),
      repeat_count: numberValue('repeatCount'),
    });
    showResult(title, data);
  } catch (error) {
    showError(title, error);
  }
}

async function callTokenCompare() {
  const title = '한국어/영어 토큰 비교 결과';
  showLoading(title);
  try {
    const data = await postJson('/api/llm/gemini/token-compare', {
      korean_text: value('koreanText'),
      english_text: value('englishText'),
    });
    showResult(title, data);
  } catch (error) {
    showError(title, error);
  }
}

async function callOpenAI() {
  const title = 'OpenAI 호환 호출 결과';
  showLoading(title);
  try {
    const data = await postJson('/api/llm/openai/chat', {
      system_instruction: value('openaiSystem'),
      user_message: value('openaiUser'),
      temperature: 0.3,
      max_output_tokens: 300,
    });
    showResult(title, data);
  } catch (error) {
    showError(title, error);
  }
}

function clearResult() {
  resultBox.textContent = '아직 실행 결과가 없습니다.';
}
