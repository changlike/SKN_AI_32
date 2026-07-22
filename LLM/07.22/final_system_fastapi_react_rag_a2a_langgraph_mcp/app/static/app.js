const chatForm = document.querySelector("#chatForm");
const messageInput = document.querySelector("#message");
const providerInput = document.querySelector("#provider");
const threadInput = document.querySelector("#threadId");
const messagesBox = document.querySelector("#messages");
const traceBox = document.querySelector("#trace");
const submitButton = chatForm.querySelector("button");

function appendMessage(role, text) {
    const article = document.createElement("article");
    article.className = `message ${role}`;
    const title = document.createElement("b");
    title.textContent = role === "user" ? "고객" : "상담원";
    const body = document.createElement("p");
    body.textContent = text;
    article.append(title, body);
    messagesBox.appendChild(article);
    messagesBox.scrollTop = messagesBox.scrollHeight;
}

function renderTrace(items) {
    traceBox.innerHTML = "";
    for (const item of items) {
        const row = document.createElement("div");
        row.className = "trace-item";
        const stage = document.createElement("b");
        stage.textContent = item.stage;
        const detail = document.createElement("span");
        detail.textContent = item.detail;
        row.append(stage, detail);
        traceBox.appendChild(row);
    }
}

chatForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const message = messageInput.value.trim();
    if (!message) return;
    appendMessage("user", message);
    messageInput.value = "";
    submitButton.disabled = true;
    submitButton.textContent = "처리 중...";
    try {
        const response = await fetch("/api/v1/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                message,
                thread_id: threadInput.value.trim() || "web-user",
                provider: providerInput.value,
            }),
        });
        const payload = await response.json();
        if (!response.ok) throw new Error(payload.detail || "API 요청에 실패했습니다.");
        appendMessage("assistant", payload.answer);
        renderTrace(payload.trace || []);
    } catch (error) {
        appendMessage("assistant", `오류: ${error.message}`);
    } finally {
        submitButton.disabled = false;
        submitButton.textContent = "통합 워크플로우 실행";
        messageInput.focus();
    }
});
