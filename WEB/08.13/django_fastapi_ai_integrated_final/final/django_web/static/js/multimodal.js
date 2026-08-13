// HTML 요소를 id로 간단히 찾기 위한 공통 함수를 정의합니다.
const byId = (id) => document.getElementById(id);

// Django CSRF 미들웨어가 검사할 csrftoken 쿠키 값을 읽습니다.
function getCsrfToken() {
    // 브라우저 쿠키 문자열을 세미콜론 기준으로 분리합니다.
    const cookies = document.cookie.split(";").map((item) => item.trim());
    // csrftoken=으로 시작하는 쿠키를 찾습니다.
    const target = cookies.find((item) => item.startsWith("csrftoken="));
    // 쿠키가 있으면 URL 디코딩한 토큰 값을 반환하고 없으면 빈 문자열을 반환합니다.
    return target ? decodeURIComponent(target.substring("csrftoken=".length)) : "";
}

// 모든 Django 프록시 POST 요청에 CSRF 헤더를 자동으로 추가합니다.
async function postForm(url, formData) {
    // 현재 Django CSRF 토큰을 읽습니다.
    const csrfToken = getCsrfToken();
    // fetch로 같은 origin의 Django API를 호출합니다.
    const response = await fetch(url, {
        method: "POST",
        headers: { "X-CSRFToken": csrfToken },
        body: formData,
        credentials: "same-origin",
    });
    // JSON 응답을 안전하게 읽습니다.
    const data = await response.json().catch(() => ({ detail: `HTTP ${response.status}` }));
    // HTTP 오류이면 Django/FastAPI detail 메시지를 예외로 전환합니다.
    if (!response.ok) throw new Error(data.detail || data.error || `HTTP ${response.status}`);
    // 정상 JSON을 반환합니다.
    return data;
}

// 화면 상단 상태 메시지를 성공/실패 공통 영역에 표시합니다.
function setStatus(message, isError = false) {
    // 상태 출력 요소를 가져옵니다.
    const target = byId("aiStatus");
    // 전달받은 메시지를 표시합니다.
    target.textContent = message;
    // 오류 여부에 따라 접근성 있는 상태 속성을 지정합니다.
    target.dataset.error = isError ? "true" : "false";
}

// FastAPI health와 MySQL 공유 연결 상태를 Django 프록시를 통해 확인합니다.
byId("healthButton").addEventListener("click", async () => {
    // 요청 시작 상태를 표시합니다.
    setStatus("FastAPI AI 서버와 MySQL 연결을 확인하고 있습니다.");
    try {
        // GET 요청은 CSRF가 필요 없으므로 직접 Django 프록시 API를 호출합니다.
        const response = await fetch("/rag/api/health/", { credentials: "same-origin" });
        // JSON 결과를 읽습니다.
        const data = await response.json();
        // 오류 상태이면 detail을 예외로 처리합니다.
        if (!response.ok) throw new Error(data.detail || "AI 서버 연결 실패");
        // 정상 서버/DB 상태를 표시합니다.
        setStatus(`FastAPI: ${data.status}, MySQL: ${data.database}`);
    } catch (error) {
        // 네트워크 또는 서버 오류를 화면에 표시합니다.
        setStatus(error.message, true);
    }
});

// 이미지 파일 선택 시 로컬 미리보기를 표시합니다.
byId("captionFile").addEventListener("change", (event) => {
    // 첫 번째 선택 파일을 읽습니다.
    const file = event.target.files[0];
    // 파일이 없으면 미리보기를 숨깁니다.
    if (!file) {
        byId("captionPreview").classList.add("hidden");
        return;
    }
    // 브라우저 메모리의 임시 URL을 생성합니다.
    byId("captionPreview").src = URL.createObjectURL(file);
    // 미리보기 이미지를 표시합니다.
    byId("captionPreview").classList.remove("hidden");
});

// 이미지 캡셔닝 폼을 Django 프록시 API에 전송합니다.
byId("captionForm").addEventListener("submit", async (event) => {
    // 일반 HTML 폼 이동을 막습니다.
    event.preventDefault();
    // 현재 폼 입력을 multipart FormData로 만듭니다.
    const formData = new FormData(event.currentTarget);
    // 처리 시작 상태를 표시합니다.
    setStatus("FastAPI에서 이미지를 분석하고 있습니다.");
    try {
        // Django가 FastAPI /api/caption으로 전달하는 프록시를 호출합니다.
        const data = await postForm("/rag/api/caption/", formData);
        // 영어 캡션을 화면에 표시합니다.
        byId("captionEnglish").textContent = data.caption_en || "";
        // 한국어 캡션을 화면에 표시합니다.
        byId("captionKorean").textContent = data.caption_ko || "";
        // 결과 영역을 표시합니다.
        byId("captionResult").classList.remove("hidden");
        // 완료 상태를 표시합니다.
        setStatus("이미지 캡셔닝이 완료되었습니다.");
    } catch (error) {
        // 오류를 상태 영역에 표시합니다.
        setStatus(error.message, true);
    }
});

// Stable Diffusion 이미지 생성 폼을 처리합니다.
byId("generateForm").addEventListener("submit", async (event) => {
    // 브라우저 기본 폼 제출을 막습니다.
    event.preventDefault();
    // 입력값을 multipart/form-data 객체로 만듭니다.
    const formData = new FormData(event.currentTarget);
    // CSRF hidden 필드는 FastAPI에 불필요하지만 Django 프록시가 받아도 문제없습니다.
    setStatus("FastAPI Stable Diffusion이 이미지를 생성하고 있습니다.");
    try {
        // Django 이미지 생성 프록시를 호출합니다.
        const data = await postForm("/rag/api/generate/", formData);
        // 실제 서비스가 사용한 프롬프트를 표시합니다.
        byId("usedPrompt").textContent = data.prompt || byId("prompt").value;
        // 재현 가능한 seed 값을 표시합니다.
        byId("usedSeed").textContent = data.seed ?? "";
        // FastAPI의 생성 이미지 절대 URL을 img src로 지정합니다.
        byId("generatedImage").src = `${data.image_url}?t=${Date.now()}`;
        // 생성 결과 영역을 표시합니다.
        byId("generateResult").classList.remove("hidden");
        // 완료 상태를 표시합니다.
        setStatus("이미지 생성이 완료되었습니다.");
    } catch (error) {
        // 모델 또는 네트워크 오류를 표시합니다.
        setStatus(error.message, true);
    }
});

// 텍스트를 FastAPI TTS로 보내고 반환 WAV를 재생하는 공통 함수를 정의합니다.
async function requestTts(text, audioElement) {
    // 비어 있는 문장은 전송하지 않습니다.
    if (!text.trim()) throw new Error("TTS로 읽을 문장을 입력하세요.");
    // FastAPI Form(text=...)와 동일한 이름으로 FormData를 구성합니다.
    const formData = new FormData();
    // 실제 텍스트를 추가합니다.
    formData.append("text", text);
    // Django 프록시를 통해 FastAPI TTS를 호출합니다.
    const data = await postForm("/rag/api/tts/", formData);
    // FastAPI WAV 절대 URL을 오디오 요소에 지정합니다.
    audioElement.src = `${data.audio_url}?t=${Date.now()}`;
    // 오디오 컨트롤을 표시합니다.
    audioElement.classList.remove("hidden");
    // 사용자 동작 직후이므로 브라우저 자동 재생 정책 범위 안에서 재생합니다.
    await audioElement.play();
}

// 이미지 캡션 한국어 문장을 TTS로 읽습니다.
byId("captionTtsButton").addEventListener("click", async () => {
    try {
        // 현재 한국어 캡션 문자열을 서버 TTS로 보냅니다.
        await requestTts(byId("captionKorean").textContent, byId("captionAudio"));
        // 완료 상태를 표시합니다.
        setStatus("한국어 캡션 TTS를 재생합니다.");
    } catch (error) {
        // TTS 오류를 표시합니다.
        setStatus(error.message, true);
    }
});

// 별도 TTS 폼의 문장을 음성으로 변환합니다.
byId("ttsForm").addEventListener("submit", async (event) => {
    // 기본 폼 제출을 막습니다.
    event.preventDefault();
    try {
        // 입력 textarea의 현재 값을 TTS로 변환합니다.
        await requestTts(byId("ttsText").value, byId("ttsAudio"));
        // 완료 상태를 표시합니다.
        setStatus("TTS 음성을 재생합니다.");
    } catch (error) {
        // 오류를 표시합니다.
        setStatus(error.message, true);
    }
});

// Web Audio API PCM 녹음 상태를 저장할 변수를 준비합니다.
let microphoneStream = null;
let audioContext = null;
let sourceNode = null;
let processorNode = null;
let silentGain = null;
let pcmChunks = [];
let recording = false;

// DataView의 지정 위치에 WAV 헤더용 ASCII 문자열을 기록합니다.
function writeAscii(view, offset, text) {
    // 문자열의 모든 문자를 순회합니다.
    for (let index = 0; index < text.length; index += 1) {
        // 문자 코드를 1바이트 값으로 기록합니다.
        view.setUint8(offset + index, text.charCodeAt(index));
    }
}

// 여러 Float32Array PCM 조각을 하나로 합칩니다.
function mergePcm(chunks) {
    // 전체 샘플 길이를 합산합니다.
    const length = chunks.reduce((sum, chunk) => sum + chunk.length, 0);
    // 전체 크기의 배열을 생성합니다.
    const merged = new Float32Array(length);
    // 복사 시작 위치를 0으로 둡니다.
    let offset = 0;
    // 각 조각을 연속해서 복사합니다.
    chunks.forEach((chunk) => { merged.set(chunk, offset); offset += chunk.length; });
    // 합친 파형을 반환합니다.
    return merged;
}

// 마이크 샘플링 주파수를 Whisper 입력용 16kHz로 선형 보간 변환합니다.
function resampleTo16k(input, sourceRate) {
    // 이미 16kHz면 복사본을 반환합니다.
    if (sourceRate === 16000) return new Float32Array(input);
    // 변환 후 필요한 샘플 수를 계산합니다.
    const outputLength = Math.max(1, Math.round(input.length * 16000 / sourceRate));
    // 결과 배열을 생성합니다.
    const output = new Float32Array(outputLength);
    // 각 출력 샘플 위치를 계산합니다.
    for (let index = 0; index < outputLength; index += 1) {
        // 원본 파형에서 대응하는 실수 위치를 계산합니다.
        const position = index * sourceRate / 16000;
        // 왼쪽 샘플 인덱스를 계산합니다.
        const left = Math.floor(position);
        // 오른쪽 샘플 인덱스를 배열 범위 안으로 제한합니다.
        const right = Math.min(left + 1, input.length - 1);
        // 두 샘플 사이 비율을 계산합니다.
        const fraction = position - left;
        // 선형 보간한 샘플 값을 저장합니다.
        output[index] = input[left] * (1 - fraction) + input[right] * fraction;
    }
    // 16kHz 파형을 반환합니다.
    return output;
}

// Float32 PCM을 16비트 mono PCM WAV Blob으로 인코딩합니다.
function encodeWav(samples, sampleRate = 16000) {
    // 44바이트 WAV 헤더와 2바이트 PCM 샘플 공간을 확보합니다.
    const buffer = new ArrayBuffer(44 + samples.length * 2);
    // 바이너리 기록용 DataView를 만듭니다.
    const view = new DataView(buffer);
    // RIFF/WAVE 표준 헤더를 기록합니다.
    writeAscii(view, 0, "RIFF"); view.setUint32(4, 36 + samples.length * 2, true); writeAscii(view, 8, "WAVE");
    writeAscii(view, 12, "fmt "); view.setUint32(16, 16, true); view.setUint16(20, 1, true); view.setUint16(22, 1, true);
    view.setUint32(24, sampleRate, true); view.setUint32(28, sampleRate * 2, true); view.setUint16(32, 2, true); view.setUint16(34, 16, true);
    writeAscii(view, 36, "data"); view.setUint32(40, samples.length * 2, true);
    // PCM 데이터 시작 위치입니다.
    let offset = 44;
    // 모든 부동소수점 샘플을 16비트 정수로 변환합니다.
    samples.forEach((sample) => {
        // -1~1 범위를 넘는 값을 잘라냅니다.
        const clipped = Math.max(-1, Math.min(1, sample));
        // 음수/양수의 16비트 최대 범위에 맞춰 정수화합니다.
        const value = clipped < 0 ? clipped * 0x8000 : clipped * 0x7fff;
        // little-endian 16비트 정수로 기록합니다.
        view.setInt16(offset, value, true);
        // 다음 샘플 위치로 이동합니다.
        offset += 2;
    });
    // 실제 WAV MIME 형식의 Blob을 반환합니다.
    return new Blob([view], { type: "audio/wav" });
}

// 녹음에 사용한 브라우저 리소스를 해제합니다.
async function releaseRecorder() {
    // ScriptProcessor 이벤트를 해제하고 연결을 끊습니다.
    if (processorNode) { processorNode.onaudioprocess = null; processorNode.disconnect(); }
    // 마이크 소스 노드를 분리합니다.
    if (sourceNode) sourceNode.disconnect();
    // 무음 gain 노드를 분리합니다.
    if (silentGain) silentGain.disconnect();
    // 브라우저 마이크 사용을 종료합니다.
    if (microphoneStream) microphoneStream.getTracks().forEach((track) => track.stop());
    // AudioContext가 열려 있으면 닫습니다.
    if (audioContext && audioContext.state !== "closed") await audioContext.close();
    // 다음 녹음을 위해 참조를 초기화합니다.
    microphoneStream = audioContext = sourceNode = processorNode = silentGain = null;
}

// 마이크 버튼을 누르면 녹음을 시작하고 다시 누르면 FastAPI STT로 전송합니다.
byId("recordButton").addEventListener("click", async () => {
    // 현재 녹음 중이 아니면 새 녹음을 시작합니다.
    if (!recording) {
        try {
            // HTTPS 또는 localhost 환경에서 사용자 마이크 권한을 요청합니다.
            microphoneStream = await navigator.mediaDevices.getUserMedia({ audio: true });
            // 브라우저 Web Audio 컨텍스트를 생성합니다.
            audioContext = new (window.AudioContext || window.webkitAudioContext)();
            // 마이크 스트림을 Web Audio 입력 노드로 변환합니다.
            sourceNode = audioContext.createMediaStreamSource(microphoneStream);
            // PCM 조각을 얻기 위한 ScriptProcessor를 생성합니다.
            processorNode = audioContext.createScriptProcessor(4096, 1, 1);
            // 출력 소리가 들리지 않도록 gain 0 노드를 만듭니다.
            silentGain = audioContext.createGain(); silentGain.gain.value = 0;
            // 새로운 녹음용 배열을 비웁니다.
            pcmChunks = [];
            // 마이크 PCM 콜백을 등록합니다.
            processorNode.onaudioprocess = (event) => pcmChunks.push(new Float32Array(event.inputBuffer.getChannelData(0)));
            // 마이크→processor→무음출력으로 연결하여 오디오 처리가 계속 실행되게 합니다.
            sourceNode.connect(processorNode); processorNode.connect(silentGain); silentGain.connect(audioContext.destination);
            // 녹음 상태를 true로 변경합니다.
            recording = true;
            // 버튼과 상태 문구를 종료 동작으로 바꿉니다.
            byId("recordButton").textContent = "⏹ 녹음 종료 및 STT"; byId("recordStatus").textContent = "녹음 중입니다. 한국어 프롬프트를 말하세요.";
        } catch (error) {
            // 마이크 권한 또는 장치 오류를 표시합니다.
            setStatus(`마이크 사용 실패: ${error.message}`, true);
        }
        // 시작 처리 후 함수 실행을 종료합니다.
        return;
    }
    // 종료 시점의 샘플링 주파수를 저장합니다.
    const sourceRate = audioContext.sampleRate;
    // 녹음 상태를 false로 변경합니다.
    recording = false;
    // 버튼을 원래 문구로 되돌립니다.
    byId("recordButton").textContent = "🎤 음성 프롬프트 녹음";
    try {
        // 녹음한 PCM 조각을 하나로 합칩니다.
        const merged = mergePcm(pcmChunks);
        // Whisper 표준 16kHz로 변환합니다.
        const pcm16k = resampleTo16k(merged, sourceRate);
        // 실제 PCM WAV 파일로 인코딩합니다.
        const wavBlob = encodeWav(pcm16k, 16000);
        // FastAPI STT 파일 업로드용 FormData를 만듭니다.
        const formData = new FormData();
        // MIME과 확장자가 모두 WAV인 File 객체를 추가합니다.
        formData.append("file", new File([wavBlob], "recording.wav", { type: "audio/wav" }));
        // 상태 문구를 변경합니다.
        byId("recordStatus").textContent = "Whisper STT 변환 중입니다.";
        // Django 프록시를 통해 FastAPI STT를 호출합니다.
        const data = await postForm("/rag/api/stt/", formData);
        // 인식된 텍스트를 이미지 생성 프롬프트 입력란에 자동 반영합니다.
        byId("prompt").value = data.text || "";
        // STT 결과 상태를 표시합니다.
        byId("recordStatus").textContent = `STT 결과: ${data.text || "인식 결과 없음"}`;
        // 전체 상태에도 완료 메시지를 표시합니다.
        setStatus("음성 프롬프트 STT 변환이 완료되었습니다.");
    } catch (error) {
        // STT 오류를 표시합니다.
        byId("recordStatus").textContent = error.message; setStatus(error.message, true);
    } finally {
        // 성공/실패와 관계없이 마이크 리소스를 해제합니다.
        await releaseRecorder();
    }
});
