"use strict";

// 이미지 생성 폼 요소를 가져옵니다.
const generationForm = document.getElementById("generation-form");

// 사용자 프롬프트 입력 필드를 가져옵니다.
const promptInput = document.getElementById("prompt-input");

// 사용자가 지정하는 Negative prompt 입력 필드를 가져옵니다.
const negativePromptInput = document.getElementById("negative-prompt-input");

// 노이즈 제거 단계 수 입력 필드를 가져옵니다.
const stepsInput = document.getElementById("steps-input");

// 프롬프트 반영 강도 입력 필드를 가져옵니다.
const guidanceInput = document.getElementById("guidance-input");

// 생성 이미지 가로 크기 입력 필드를 가져옵니다.
const widthInput = document.getElementById("width-input");

// 생성 이미지 세로 크기 입력 필드를 가져옵니다.
const heightInput = document.getElementById("height-input");

// 중간 이미지 저장 간격 입력 필드를 가져옵니다.
const saveIntervalInput = document.getElementById("save-interval-input");

// 재현용 난수 시드 입력 필드를 가져옵니다.
const seedInput = document.getElementById("seed-input");

// 마이크 녹음 시작 및 중지 버튼을 가져옵니다.
const microphoneButton = document.getElementById("microphone-button");

// 이미지 생성 요청 버튼을 가져옵니다.
const generateButton = document.getElementById("generate-button");

// 마이크 상태 관련 요소를 가져옵니다.
const microphoneStatus = document.getElementById("microphone-status");
const microphoneStatusText = document.getElementById("microphone-status-text");

// 저장된 녹음 파일과 STT 파일 링크 요소를 가져옵니다.
const recordingLinks = document.getElementById("recording-links");
const audioLink = document.getElementById("audio-link");
const transcriptLink = document.getElementById("transcript-link");

// 프롬프트 자동 변환 결과 패널의 요소를 가져옵니다.
const translationSection = document.getElementById("translation-section");
const languageBadge = document.getElementById("language-badge");
const cleanedPromptDisplay = document.getElementById("cleaned-prompt-display");
const translatedPromptDisplay = document.getElementById("translated-prompt-display");
const enhancedPromptDisplay = document.getElementById("enhanced-prompt-display");
const finalNegativeDisplay = document.getElementById("final-negative-display");

// 생성 진행 상태 관련 요소를 가져옵니다.
const progressSection = document.getElementById("progress-section");
const statusBadge = document.getElementById("status-badge");
const jobMessage = document.getElementById("job-message");
const progressBar = document.getElementById("progress-bar");
const stepProgress = document.getElementById("step-progress");
const seedDisplay = document.getElementById("seed-display");

// 최종 생성 결과 관련 요소를 가져옵니다.
const resultSection = document.getElementById("result-section");
const finalImage = document.getElementById("final-image");
const resultPrompt = document.getElementById("result-prompt");
const resultTranslatedPrompt = document.getElementById("result-translated-prompt");
const resultNegativePrompt = document.getElementById("result-negative-prompt");
const resultOptions = document.getElementById("result-options");
const metadataLink = document.getElementById("metadata-link");

// 단계별 이미지 갤러리 관련 요소를 가져옵니다.
const stepsSection = document.getElementById("steps-section");
const stepsGallery = document.getElementById("steps-gallery");
const imageCountBadge = document.getElementById("image-count-badge");

// 오류 표시 관련 요소를 가져옵니다.
const errorSection = document.getElementById("error-section");
const errorMessage = document.getElementById("error-message");

// 현재 MediaRecorder 객체를 저장할 변수를 선언합니다.
let mediaRecorder = null;

// 현재 마이크 MediaStream 객체를 저장할 변수를 선언합니다.
let mediaStream = null;

// 녹음 중 수집되는 음성 Blob 조각을 저장할 배열을 선언합니다.
let audioChunks = [];

// 현재 녹음 중인지 저장할 상태값을 선언합니다.
let isRecording = false;

// 너무 짧은 녹음을 차단하기 위해 녹음 시작 시각을 저장합니다.
let recordingStartedAt = 0;

// 사용자가 최소한 말해야 하는 시간을 밀리초로 지정합니다.
const MINIMUM_RECORDING_MS = 1200;

// 이미 화면에 추가한 중간 이미지 URL을 추적할 집합을 생성합니다.
const renderedStepUrls = new Set();


// 마이크 상태 상자의 색상과 메시지를 변경합니다.
function updateMicrophoneStatus(stateClass, message) {
    // 이전 상태 클래스를 모두 제거합니다.
    microphoneStatus.classList.remove(
        "idle",
        "recording",
        "processing",
        "completed"
    );

    // 전달받은 현재 상태 클래스를 추가합니다.
    microphoneStatus.classList.add(stateClass);

    // 전달받은 메시지를 상태 문구로 표시합니다.
    microphoneStatusText.textContent = message;
}


// 기존 오류 메시지를 화면에서 제거합니다.
function clearError() {
    // 오류 패널을 숨깁니다.
    errorSection.classList.add("hidden");

    // 기존 오류 문구를 비웁니다.
    errorMessage.textContent = "";
}


// 새로운 오류 메시지를 화면에 표시합니다.
function showError(message) {
    // 전달받은 오류 문구를 설정합니다.
    errorMessage.textContent = message;

    // 오류 패널을 화면에 표시합니다.
    errorSection.classList.remove("hidden");
}


// 서버 오류 응답에서 사람이 읽을 메시지를 추출합니다.
async function extractErrorMessage(response) {
    // 응답이 JSON이 아닐 가능성을 처리하기 위해 try 블록을 시작합니다.
    try {
        // 서버 응답을 JSON 객체로 읽습니다.
        const data = await response.json();

        // detail 값이 문자열인지 확인합니다.
        if (typeof data.detail === "string") {
            // 문자열 오류를 그대로 반환합니다.
            return data.detail;
        }

        // detail 값이 존재하는지 확인합니다.
        if (data.detail) {
            // 객체 또는 배열 오류를 JSON 문자열로 변환합니다.
            return JSON.stringify(data.detail);
        }
    } catch (error) {
        // JSON 파싱 실패 원인을 개발자 도구에 기록합니다.
        console.error("오류 응답 파싱 실패:", error);
    }

    // 구체적인 오류가 없으면 HTTP 상태 코드를 포함한 기본 문구를 반환합니다.
    return `요청 처리에 실패했습니다. HTTP ${response.status}`;
}


// 브라우저가 지원하는 가장 적절한 녹음 MIME 타입을 찾습니다.
function selectSupportedMimeType() {
    // 우선적으로 확인할 음성 형식 목록을 정의합니다.
    const candidates = [
        "audio/webm;codecs=opus",
        "audio/webm",
        "audio/ogg;codecs=opus",
        "audio/mp4"
    ];

    // 각 후보 형식을 순서대로 확인합니다.
    for (const mimeType of candidates) {
        // 현재 브라우저가 해당 형식을 지원하는지 검사합니다.
        if (MediaRecorder.isTypeSupported(mimeType)) {
            // 지원되는 첫 번째 형식을 반환합니다.
            return mimeType;
        }
    }

    // 지원 형식을 특정할 수 없으면 브라우저 기본값을 사용합니다.
    return "";
}


// 브라우저 마이크 녹음을 시작합니다.
async function startRecording() {
    // 이전 오류 메시지를 제거합니다.
    clearError();

    // 현재 브라우저가 마이크 및 MediaRecorder API를 지원하는지 확인합니다.
    if (!navigator.mediaDevices || !window.MediaRecorder) {
        // 지원하지 않으면 오류를 표시합니다.
        showError("현재 브라우저는 마이크 녹음 기능을 지원하지 않습니다.");
        return;
    }

    // 권한 요청과 녹음 객체 생성 중 발생하는 오류를 처리합니다.
    try {
        // 사용자 마이크 입력 스트림을 요청합니다.
        mediaStream = await navigator.mediaDevices.getUserMedia({
            audio: {
                echoCancellation: true,
                noiseSuppression: true,
                autoGainControl: true,
                channelCount: 1
            }
        });

        // 현재 브라우저가 지원하는 녹음 MIME 타입을 선택합니다.
        const mimeType = selectSupportedMimeType();

        // 형식을 지정할 수 있으면 옵션과 함께 녹음 객체를 생성합니다.
        mediaRecorder = mimeType
            ? new MediaRecorder(mediaStream, { mimeType })
            : new MediaRecorder(mediaStream);

        // 새 녹음을 시작하므로 기존 음성 조각을 초기화합니다.
        audioChunks = [];

        // 녹음 데이터 조각이 준비될 때마다 실행할 이벤트를 등록합니다.
        mediaRecorder.addEventListener("dataavailable", (event) => {
            // 비어 있지 않은 데이터만 배열에 추가합니다.
            if (event.data && event.data.size > 0) {
                audioChunks.push(event.data);
            }
        });

        // 녹음이 중지되면 서버 업로드 함수를 실행합니다.
        mediaRecorder.addEventListener("stop", uploadRecordedAudio);

        // 250ms마다 음성 조각을 생성하여 짧은 녹음에서도 데이터가 안정적으로 수집되게 합니다.
        mediaRecorder.start(250);

        // 최소 녹음 시간을 계산하기 위해 시작 시각을 기록합니다.
        recordingStartedAt = Date.now();

        // 현재 녹음 상태를 true로 변경합니다.
        isRecording = true;

        // 마이크 버튼에 녹음 중 시각 효과를 적용합니다.
        microphoneButton.classList.add("recording");

        // 접근성 문구를 녹음 중지로 변경합니다.
        microphoneButton.setAttribute("aria-label", "마이크 녹음 중지");

        // 화면에 마이크 사용 중 상태를 표시합니다.
        updateMicrophoneStatus(
            "recording",
            "마이크 사용 중 · 말씀을 마치면 아이콘을 다시 누르세요."
        );
    } catch (error) {
        // 마이크 권한 또는 장치 오류를 개발자 도구에 기록합니다.
        console.error("마이크 시작 오류:", error);

        // 사용자에게 권한과 장치 확인 메시지를 표시합니다.
        showError(
            "마이크를 시작하지 못했습니다. 브라우저의 마이크 권한을 확인하세요."
        );

        // 상태를 대기 상태로 되돌립니다.
        updateMicrophoneStatus("idle", "마이크 사용 실패");
    }
}


// 현재 마이크 녹음을 중지합니다.
function stopRecording() {
    // 녹음 객체가 없거나 녹음 중이 아니면 함수를 종료합니다.
    if (!mediaRecorder || !isRecording) {
        return;
    }

    // 실제 녹음 시간을 계산합니다.
    const recordedMilliseconds = Date.now() - recordingStartedAt;

    // 너무 빠르게 다시 누르면 말소리가 거의 기록되지 않으므로 녹음을 계속 유지합니다.
    if (recordedMilliseconds < MINIMUM_RECORDING_MS) {
        updateMicrophoneStatus(
            "recording",
            "녹음 시간이 너무 짧습니다 · 2초 이상 말한 뒤 다시 눌러 주세요."
        );
        return;
    }

    // 마지막 버퍼 조각을 즉시 요청한 다음 MediaRecorder를 중지합니다.
    if (mediaRecorder.state === "recording") {
        mediaRecorder.requestData();
    }
    mediaRecorder.stop();

    // 녹음 상태를 false로 변경합니다.
    isRecording = false;

    // 마이크 버튼의 녹음 중 스타일을 제거합니다.
    microphoneButton.classList.remove("recording");

    // 접근성 문구를 다시 녹음 시작으로 변경합니다.
    microphoneButton.setAttribute("aria-label", "마이크 녹음 시작");

    // 음성 저장 및 STT 처리 중임을 표시합니다.
    updateMicrophoneStatus(
        "processing",
        "녹음을 저장하고 음성을 텍스트로 변환하고 있습니다."
    );

    // 마이크 스트림이 존재하는지 확인합니다.
    if (mediaStream) {
        // 모든 입력 트랙을 중지하여 마이크 장치 점유를 해제합니다.
        mediaStream.getTracks().forEach((track) => track.stop());
    }
}


// 녹음된 음성을 FastAPI에 업로드하고 STT 결과를 받습니다.
async function uploadRecordedAudio() {
    // 이전 오류를 제거합니다.
    clearError();

    // 실제 녹음 MIME 타입 또는 기본 webm 타입을 결정합니다.
    const mimeType = mediaRecorder?.mimeType || "audio/webm";

    // 수집한 음성 조각을 하나의 Blob으로 결합합니다.
    const audioBlob = new Blob(audioChunks, {
        type: mimeType
    });

    // 음성 데이터가 비어 있는지 확인합니다.
    if (audioBlob.size === 0) {
        // 빈 녹음 오류를 표시합니다.
        showError("녹음된 음성 데이터가 없습니다.");

        // 마이크 상태를 대기 상태로 변경합니다.
        updateMicrophoneStatus("idle", "마이크 대기 상태");
        return;
    }

    // multipart 파일 업로드에 사용할 FormData 객체를 생성합니다.
    const formData = new FormData();

    // MIME 타입에 맞는 파일 확장자를 결정합니다.
    const extension = mimeType.includes("ogg")
        ? "ogg"
        : mimeType.includes("mp4")
            ? "m4a"
            : "webm";

    // 음성 Blob을 audio 필드와 파일명으로 추가합니다.
    formData.append(
        "audio",
        audioBlob,
        `recording.${extension}`
    );

    // STT API 호출 오류를 처리합니다.
    try {
        // 음성 파일을 STT 엔드포인트로 전송합니다.
        const response = await fetch("/api/stt/transcribe", {
            method: "POST",
            body: formData
        });

        // 응답 상태가 성공이 아닌지 확인합니다.
        if (!response.ok) {
            // 서버 오류 메시지를 이용해 예외를 발생시킵니다.
            throw new Error(await extractErrorMessage(response));
        }

        // STT 성공 응답을 JSON으로 읽습니다.
        const data = await response.json();

        // 변환된 텍스트를 이미지 프롬프트 입력창에 자동 입력합니다.
        promptInput.value = data.text;

        // 녹음 파일 링크를 설정합니다.
        audioLink.href = data.audio_url;

        // STT 텍스트 파일 링크를 설정합니다.
        transcriptLink.href = data.transcript_url;

        // 파일 링크를 화면에 표시합니다.
        recordingLinks.classList.remove("hidden");

        // STT 완료 상태를 표시합니다.
        updateMicrophoneStatus(
            "completed",
            "STT 변환 완료 · 한국어 문장을 프롬프트에 입력했습니다."
        );

        // 사용자가 프롬프트를 확인하도록 입력 필드에 포커스를 둡니다.
        promptInput.focus();
    } catch (error) {
        // STT 오류를 개발자 도구에 기록합니다.
        console.error("STT 처리 오류:", error);

        // 실제 오류 문구를 화면에 표시합니다.
        showError(error.message);

        // 마이크 상태를 실패 상태로 표시합니다.
        updateMicrophoneStatus("idle", "STT 처리 실패");
    }
}


// 마이크 버튼 클릭 시 녹음 시작 또는 중지를 실행합니다.
microphoneButton.addEventListener("click", async () => {
    // 현재 녹음 중인지 확인합니다.
    if (isRecording) {
        // 녹음 중이면 중지합니다.
        stopRecording();
        return;
    }

    // 녹음 중이 아니면 새 녹음을 시작합니다.
    await startRecording();
});


// 새 생성 요청 전에 이전 진행 및 결과 화면을 초기화합니다.
function resetGenerationView() {
    // 기존 오류를 숨깁니다.
    clearError();

    // 번역 결과 패널을 우선 숨깁니다.
    translationSection.classList.add("hidden");

    // 생성 진행 패널을 화면에 표시합니다.
    progressSection.classList.remove("hidden");

    // 이전 최종 결과 패널을 숨깁니다.
    resultSection.classList.add("hidden");

    // 이전 단계별 이미지 패널을 숨깁니다.
    stepsSection.classList.add("hidden");

    // 기존 단계별 이미지 카드를 모두 제거합니다.
    stepsGallery.innerHTML = "";

    // 중복 이미지 URL 집합을 초기화합니다.
    renderedStepUrls.clear();

    // 진행률 막대를 0%로 초기화합니다.
    progressBar.style.width = "0%";

    // 상태 배지를 접수 중으로 변경합니다.
    statusBadge.textContent = "접수 중";

    // 현재 메시지를 작업 등록 문구로 변경합니다.
    jobMessage.textContent = "이미지 생성 작업을 서버에 등록하고 있습니다.";

    // 단계 진행 문구를 초기화합니다.
    stepProgress.textContent = "0 / 0 단계";

    // 시드 표시를 초기화합니다.
    seedDisplay.textContent = "Seed: -";
}


// 프롬프트 변환 정보를 화면에 표시합니다.
function renderPromptPreparation(job) {
    // 번역 또는 보강 정보가 한 가지라도 존재하는지 확인합니다.
    if (
        !job.cleaned_prompt
        && !job.translated_prompt
        && !job.enhanced_prompt
    ) {
        // 아직 준비되지 않았다면 함수를 종료합니다.
        return;
    }

    // 정리된 원문을 표시합니다.
    cleanedPromptDisplay.textContent = job.cleaned_prompt || job.prompt;

    // 영어 번역 결과를 표시합니다.
    translatedPromptDisplay.textContent =
        job.translated_prompt || job.cleaned_prompt || job.prompt;

    // 실제 이미지 모델에 전달한 보강 프롬프트를 표시합니다.
    enhancedPromptDisplay.textContent =
        job.enhanced_prompt || job.translated_prompt || job.prompt;

    // 자동 보정이 적용된 최종 Negative prompt를 표시합니다.
    finalNegativeDisplay.textContent =
        job.final_negative_prompt || job.negative_prompt || "사용하지 않음";

    // 한글 감지 여부에 맞는 배지 문구를 표시합니다.
    languageBadge.textContent = job.korean_detected
        ? "한국어 → 영어 자동 번역"
        : "영어 프롬프트";

    // 번역 결과 패널을 화면에 표시합니다.
    translationSection.classList.remove("hidden");
}


// 새 단계별 이미지 카드를 화면에 추가합니다.
function renderStepImages(stepImages, saveInterval, totalSteps) {
    // 전달받은 이미지 URL 목록을 순서대로 반복합니다.
    stepImages.forEach((imageUrl, index) => {
        // 이미 화면에 추가한 URL인지 확인합니다.
        if (renderedStepUrls.has(imageUrl)) {
            // 중복 URL이면 현재 항목을 건너뜁니다.
            return;
        }

        // 현재 URL을 렌더링 완료 집합에 추가합니다.
        renderedStepUrls.add(imageUrl);

        // 이미지 카드 전체를 감쌀 요소를 생성합니다.
        const card = document.createElement("article");

        // 카드 디자인 클래스 이름을 지정합니다.
        card.className = "step-card";

        // 중간 이미지를 표시할 img 요소를 생성합니다.
        const image = document.createElement("img");

        // 브라우저 캐시를 피하기 위해 현재 시각을 URL에 추가합니다.
        image.src = `${imageUrl}?t=${Date.now()}`;

        // 접근성을 위한 대체 텍스트를 지정합니다.
        image.alt = `디퓨전 중간 단계 이미지 ${index + 1}`;

        // 단계 번호 설명을 표시할 문단을 생성합니다.
        const caption = document.createElement("p");

        // URL 파일명에서 실제 단계 번호를 추출합니다.
        const match = imageUrl.match(/step_(\d+)\.png$/);

        // URL에 번호가 없을 때 사용할 단계 번호를 계산합니다.
        const calculatedStep = Math.min(
            (index + 1) * saveInterval,
            totalSteps
        );

        // 실제 파일명 번호 또는 계산 번호를 선택합니다.
        const stepNumber = match
            ? Number.parseInt(match[1], 10)
            : calculatedStep;

        // 카드에 현재 단계 번호를 표시합니다.
        caption.textContent = `Step ${stepNumber}`;

        // 이미지와 설명을 카드에 추가합니다.
        card.append(image, caption);

        // 완성된 카드를 갤러리에 추가합니다.
        stepsGallery.appendChild(card);
    });

    // 현재 이미지 수를 배지에 표시합니다.
    imageCountBadge.textContent = `${renderedStepUrls.size}장`;

    // 이미지가 한 장 이상 존재하는지 확인합니다.
    if (renderedStepUrls.size > 0) {
        // 단계별 이미지 패널을 화면에 표시합니다.
        stepsSection.classList.remove("hidden");
    }
}


// 서버에서 받은 작업 상태를 화면에 반영합니다.
function updateGenerationView(job) {
    // 서버 상태를 사용자용 한글 문구로 연결합니다.
    const statusLabels = {
        queued: "대기",
        preparing_prompt: "프롬프트 분석",
        loading: "모델 로딩",
        running: "생성 중",
        completed: "완료",
        failed: "실패"
    };

    // 현재 상태 배지 문구를 설정합니다.
    statusBadge.textContent = statusLabels[job.status] || job.status;

    // 현재 작업 메시지를 표시합니다.
    jobMessage.textContent = job.message || "작업 상태를 확인하고 있습니다.";

    // 진행률을 숫자로 변환하고 0~100 범위로 제한합니다.
    const progress = Math.max(
        0,
        Math.min(100, Number(job.progress || 0))
    );

    // 진행률 막대 너비를 갱신합니다.
    progressBar.style.width = `${progress}%`;

    // 현재 단계와 전체 추론 단계 수를 표시합니다.
    stepProgress.textContent =
        `${job.current_step || 0} / ${job.inference_steps || 0} 단계`;

    // 실제 생성에 사용한 시드를 표시합니다.
    seedDisplay.textContent = `Seed: ${job.seed}`;

    // 번역 및 프롬프트 보강 정보를 화면에 반영합니다.
    renderPromptPreparation(job);

    // 단계별 이미지 배열이 존재하는지 확인합니다.
    if (Array.isArray(job.step_images)) {
        // 새로 저장된 중간 이미지를 갤러리에 추가합니다.
        renderStepImages(
            job.step_images,
            job.save_interval,
            job.inference_steps
        );
    }

    // 작업이 완료되고 최종 이미지 URL이 존재하는지 확인합니다.
    if (job.status === "completed" && job.final_image_url) {
        // 브라우저 캐시를 방지한 최종 이미지 URL을 설정합니다.
        finalImage.src = `${job.final_image_url}?t=${Date.now()}`;

        // 사용자가 입력한 원본 프롬프트를 표시합니다.
        resultPrompt.textContent = job.prompt;

        // 한국어를 번역한 영어 프롬프트를 표시합니다.
        resultTranslatedPrompt.textContent =
            job.translated_prompt || job.prompt;

        // 실제 추론에 사용한 최종 Negative prompt를 표시합니다.
        resultNegativePrompt.textContent =
            job.final_negative_prompt || job.negative_prompt || "사용하지 않음";

        // 주요 생성 설정을 한 문장으로 표시합니다.
        resultOptions.textContent =
            `Model ${job.model_id || "configured model"}, ` +
            `Steps ${job.inference_steps}, ` +
            `Guidance ${job.guidance_scale}, ` +
            `${job.width}×${job.height}, ` +
            `Seed ${job.seed}`;

        // 메타데이터 JSON 링크를 설정합니다.
        metadataLink.href = job.metadata_url;

        // 최종 결과 패널을 화면에 표시합니다.
        resultSection.classList.remove("hidden");
    }
}


// 이미지 생성 작업 상태를 완료 또는 실패까지 반복 조회합니다.
async function pollGenerationJob(jobId) {
    // 작업이 종료될 때까지 반복합니다.
    while (true) {
        // 서버 부하를 줄이기 위해 1.5초 기다립니다.
        await new Promise((resolve) => setTimeout(resolve, 1500));

        // 현재 작업 상태 엔드포인트를 호출합니다.
        const response = await fetch(`/api/generations/${jobId}`);

        // 상태 조회가 실패했는지 확인합니다.
        if (!response.ok) {
            // 서버 오류 메시지로 예외를 발생시킵니다.
            throw new Error(await extractErrorMessage(response));
        }

        // 현재 작업 상태 JSON을 읽습니다.
        const job = await response.json();

        // 상태 정보를 화면에 반영합니다.
        updateGenerationView(job);

        // 작업이 정상 완료되었는지 확인합니다.
        if (job.status === "completed") {
            // 이미지 생성 버튼을 다시 활성화합니다.
            generateButton.disabled = false;

            // 상태 조회 반복을 종료합니다.
            return;
        }

        // 작업이 실패했는지 확인합니다.
        if (job.status === "failed") {
            // 서버가 저장한 오류 메시지로 예외를 발생시킵니다.
            throw new Error(job.message || "이미지 생성 작업에 실패했습니다.");
        }
    }
}


// 생성 폼을 제출하면 번역 및 SDXL 이미지 생성 작업을 등록합니다.
generationForm.addEventListener("submit", async (event) => {
    // 브라우저 기본 폼 전송과 페이지 새로고침을 막습니다.
    event.preventDefault();

    // 모든 폼 입력값을 읽고 필요한 타입으로 변환합니다.
    const prompt = promptInput.value.trim();
    const negativePrompt = negativePromptInput.value.trim();
    const inferenceSteps = Number.parseInt(stepsInput.value, 10);
    const guidanceScale = Number.parseFloat(guidanceInput.value);
    const width = Number.parseInt(widthInput.value, 10);
    const height = Number.parseInt(heightInput.value, 10);
    const saveInterval = Number.parseInt(saveIntervalInput.value, 10);
    const rawSeed = seedInput.value.trim();

    // 프롬프트가 비어 있는지 확인합니다.
    if (!prompt) {
        // 필수 프롬프트 입력 오류를 표시합니다.
        showError("생성할 이미지의 프롬프트를 입력하세요.");
        return;
    }

    // 이미지 크기가 8의 배수인지 확인합니다.
    if (width % 8 !== 0 || height % 8 !== 0) {
        // 잠재 공간 크기 규칙 오류를 표시합니다.
        showError("이미지 가로와 세로 크기는 모두 8의 배수여야 합니다.");
        return;
    }

    // 시드가 비어 있으면 null로, 입력되었으면 정수로 변환합니다.
    const seed = rawSeed === ""
        ? null
        : Number.parseInt(rawSeed, 10);

    // 이전 생성 화면을 초기화합니다.
    resetGenerationView();

    // 중복 요청을 막기 위해 생성 버튼을 비활성화합니다.
    generateButton.disabled = true;

    // 작업 접수 및 상태 조회 오류를 처리합니다.
    try {
        // 이미지 생성 작업 접수 API를 호출합니다.
        const response = await fetch("/api/generations", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                prompt,
                negative_prompt: negativePrompt,
                inference_steps: inferenceSteps,
                guidance_scale: guidanceScale,
                width,
                height,
                save_interval: saveInterval,
                seed
            })
        });

        // 접수 응답이 성공 상태가 아닌지 확인합니다.
        if (!response.ok) {
            // 서버 오류 메시지를 추출하여 예외를 발생시킵니다.
            throw new Error(await extractErrorMessage(response));
        }

        // 접수 결과 JSON을 읽습니다.
        const acceptedJob = await response.json();

        // 실제 서버가 결정한 시드를 표시합니다.
        seedDisplay.textContent = `Seed: ${acceptedJob.seed}`;

        // 접수된 작업의 상태 조회를 시작합니다.
        await pollGenerationJob(acceptedJob.job_id);
    } catch (error) {
        // 이미지 생성 오류를 개발자 도구에 기록합니다.
        console.error("이미지 생성 오류:", error);

        // 실제 오류 메시지를 사용자 화면에 표시합니다.
        showError(error.message);

        // 상태 배지를 실패로 변경합니다.
        statusBadge.textContent = "실패";

        // 재시도할 수 있도록 생성 버튼을 활성화합니다.
        generateButton.disabled = false;
    }
});
