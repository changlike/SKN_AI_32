/*
 * FastAPI와 vLLM 상태 확인 및 한국어 채팅 요청을 처리합니다.
 */

/**
 * JSON API를 호출하고 오류를 일관된 예외로 변환합니다.
 */
async function requestJson(url, options = {}) {
    // fetch로 지정된 URL에 HTTP 요청을 전송합니다.
    const response = await fetch(url, options);

    // 서버 응답 본문을 JSON으로 해석합니다.
    const data = await response.json();

    // 성공 상태가 아니면 서버 detail 또는 기본 메시지로 오류를 발생시킵니다.
    if (!response.ok) {
        throw new Error(data.detail || "API 요청에 실패했습니다.");
    }

    // 정상 JSON 데이터를 반환합니다.
    return data;
}

/**
 * 객체를 보기 좋은 JSON 문자열로 변환해 화면에 표시합니다.
 */
function showJson(elementId, data) {
    // 대상 요소를 ID로 찾습니다.
    const element = document.getElementById(elementId);

    // 두 칸 들여쓰기 JSON 문자열을 요소에 표시합니다.
    element.textContent = JSON.stringify(data, null, 2);
}

// FastAPI 상태 확인 버튼 이벤트를 등록합니다.
document.getElementById("fastapiHealthButton").addEventListener("click", async () => {
    try {
        // 확인 중 메시지를 표시합니다.
        document.getElementById("healthResult").textContent = "FastAPI 상태 확인 중...";

        // FastAPI 자체 상태 API를 호출합니다.
        const data = await requestJson("/api/system/health");

        // 결과를 화면에 표시합니다.
        showJson("healthResult", data);
    } catch (error) {
        // 오류 메시지를 화면에 표시합니다.
        showJson("healthResult", {error: error.message});
    }
});

// vLLM 상태 확인 버튼 이벤트를 등록합니다.
document.getElementById("vllmHealthButton").addEventListener("click", async () => {
    try {
        // 확인 중 메시지를 표시합니다.
        document.getElementById("healthResult").textContent = "vLLM 상태 확인 중...";

        // FastAPI를 통해 vLLM 모델 목록을 조회합니다.
        const data = await requestJson("/api/system/vllm-health");

        // 결과를 화면에 표시합니다.
        showJson("healthResult", data);
    } catch (error) {
        // 오류 메시지를 화면에 표시합니다.
        showJson("healthResult", {error: error.message});
    }
});

// 채팅 답변 생성 버튼 이벤트를 등록합니다.
document.getElementById("chatButton").addEventListener("click", async () => {
    try {
        // 시스템 프롬프트를 읽습니다.
        const systemPrompt = document.getElementById("systemPrompt").value.trim();

        // 사용자 질문을 읽습니다.
        const message = document.getElementById("message").value.trim();

        // Temperature 값을 숫자로 변환합니다.
        const temperature = Number(document.getElementById("temperature").value);

        // 최대 출력 토큰을 숫자로 변환합니다.
        const maxTokens = Number(document.getElementById("maxTokens").value);

        // 필수 입력값이 비어 있는지 확인합니다.
        if (!systemPrompt || !message) {
            throw new Error("System Prompt와 질문을 입력하세요.");
        }

        // 추론 수행 중 메시지를 표시합니다.
        document.getElementById("chatResult").textContent = "vLLM 모델이 답변을 생성하고 있습니다...";

        // FastAPI 채팅 API에 JSON 요청을 전송합니다.
        const data = await requestJson("/api/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                message: message,
                system_prompt: systemPrompt,
                history: [],
                temperature: temperature,
                top_p: 0.9,
                max_tokens: maxTokens
            })
        });

        // 모델 답변과 성능 정보를 표시합니다.
        showJson("chatResult", data);
    } catch (error) {
        // 오류 메시지를 표시합니다.
        showJson("chatResult", {error: error.message});
    }
});
