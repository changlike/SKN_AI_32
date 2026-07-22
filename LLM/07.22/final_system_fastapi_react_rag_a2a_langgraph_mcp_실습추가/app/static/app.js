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

// ── 탭 전환 로직 ──────────────────────────────────────────────
// tabButtons는 상단 탭 버튼 전체 목록입니다.
const tabButtons = document.querySelectorAll(".tab-btn");
// tabPanels는 각 탭에 대응하는 콘텐츠 영역 전체 목록입니다.
const tabPanels = document.querySelectorAll(".tab-panel");

tabButtons.forEach((button) => {
    button.addEventListener("click", () => {
        // 모든 버튼과 패널에서 active 클래스를 제거합니다.
        tabButtons.forEach((btn) => btn.classList.remove("active"));
        tabPanels.forEach((panel) => panel.classList.remove("active"));
        // 클릭한 버튼과 data-tab 값이 같은 패널만 active로 전환합니다.
        button.classList.add("active");
        document.getElementById(button.dataset.tab).classList.add("active");
    });
});

// ── 탭 2: 문의 처리 연계 부서 연결 ────────────────────────────
const complaintForm = document.querySelector("#complaintForm");
const complaintCustomerIdInput = document.querySelector("#complaintCustomerId");
const complaintMessageInput = document.querySelector("#complaintMessage");
const complaintResultBox = document.querySelector("#complaintResult");

complaintForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const customerId = complaintCustomerIdInput.value.trim();
    const message = complaintMessageInput.value.trim();
    if (!message) return;
    const submitButton = complaintForm.querySelector("button");
    submitButton.disabled = true;
    submitButton.textContent = "접수 처리 중...";
    try {
        const response = await fetch("/api/v1/complaints/handle", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ customer_id: customerId || "web-guest", message }),
        });
        const payload = await response.json();
        if (!response.ok) throw new Error(payload.detail || "API 요청에 실패했습니다.");
        // matched 여부에 따라 접수 결과 문구를 다르게 구성합니다.
        complaintResultBox.className = `complaint-result ${payload.matched ? "matched" : "unmatched"}`;
        complaintResultBox.innerHTML = payload.matched
            ? `<b>${payload.answer}</b><span>접수번호 cc_id=${payload.cc_id} · 담당부서 ${payload.dept_id}</span>`
            : `<b>${payload.answer}</b>`;
        complaintMessageInput.value = "";
    } catch (error) {
        complaintResultBox.className = "complaint-result unmatched";
        complaintResultBox.innerHTML = `<b>오류: ${error.message}</b>`;
    } finally {
        submitButton.disabled = false;
        submitButton.textContent = "문의 접수";
    }
});

// ── 탭 3: 요약 보고서 만들기 ──────────────────────────────────
const summaryReportForm = document.querySelector("#summaryReportForm");
const summaryProviderInput = document.querySelector("#summaryProvider");
const summaryReportResultBox = document.querySelector("#summaryReportResult");

summaryReportForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const submitButton = summaryReportForm.querySelector("button");
    submitButton.disabled = true;
    submitButton.textContent = "요약 생성 중...";
    try {
        const response = await fetch("/api/v1/reports/inquiry-summary", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ provider: summaryProviderInput.value }),
        });
        const payload = await response.json();
        if (!response.ok) throw new Error(payload.detail || "API 요청에 실패했습니다.");
        // 핵심 집계 카드와 LLM 서술 요약, 저장 경로를 함께 표시합니다.
        summaryReportResultBox.className = "report-result visible";
        summaryReportResultBox.innerHTML = `
            <div class="report-stats">
                <div class="stat"><b>${payload.total_count}건</b><span>전체 문의</span></div>
                <div class="stat"><b>${payload.top_category}</b><span>최다 유형 (${payload.top_category_pct}%)</span></div>
                <div class="stat"><b>${payload.top_category_count}건</b><span>최다 유형 건수</span></div>
            </div>
            <div class="report-markdown">${payload.report_markdown}</div>
            <p class="report-saved">저장 위치: ${payload.saved_path}</p>
        `;
    } catch (error) {
        summaryReportResultBox.className = "report-result visible";
        summaryReportResultBox.innerHTML = `<b>오류: ${error.message}</b>`;
    } finally {
        submitButton.disabled = false;
        submitButton.textContent = "요약 보고서 생성";
    }
});

// ── 탭 4: 임원용 매출 보고서 만들기 ────────────────────────────
const salesReportForm = document.querySelector("#salesReportForm");
const salesMonthInput = document.querySelector("#salesMonth");
const salesProviderInput = document.querySelector("#salesProvider");
const salesReportResultBox = document.querySelector("#salesReportResult");

salesReportForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const submitButton = salesReportForm.querySelector("button");
    submitButton.disabled = true;
    submitButton.textContent = "보고서 생성 중...";
    try {
        const response = await fetch("/api/v1/reports/executive-sales", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                month: salesMonthInput.value.trim() || null,
                provider: salesProviderInput.value,
            }),
        });
        const payload = await response.json();
        if (!response.ok) throw new Error(payload.detail || "API 요청에 실패했습니다.");
        // 핵심 수치 카드와 LLM 서술 보고서, 저장 경로를 함께 표시합니다.
        salesReportResultBox.className = "report-result visible";
        salesReportResultBox.innerHTML = `
            <div class="report-stats">
                <div class="stat"><b>${payload.month}</b><span>대상 월</span></div>
                <div class="stat"><b>${payload.total.toLocaleString()}원</b><span>총매출</span></div>
                <div class="stat"><b>${payload.growth_pct > 0 ? "+" : ""}${payload.growth_pct}%</b><span>전월(${payload.prev_month}) 대비</span></div>
                <div class="stat"><b>${payload.top_category}</b><span>매출 1위 카테고리</span></div>
            </div>
            <div class="report-markdown">${payload.report_markdown}</div>
            <p class="report-saved">저장 위치: ${payload.saved_path}</p>
        `;
    } catch (error) {
        salesReportResultBox.className = "report-result visible";
        salesReportResultBox.innerHTML = `<b>오류: ${error.message}</b>`;
    } finally {
        submitButton.disabled = false;
        submitButton.textContent = "보고서 생성";
    }
});

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
