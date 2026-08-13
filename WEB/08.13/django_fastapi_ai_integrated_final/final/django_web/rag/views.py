"""Django 화면과 FastAPI AI 파이프라인 사이를 연결하는 게이트웨이 View입니다."""
# FastAPI 응답의 파일명을 안전하게 인코딩하기 위해 quote를 가져옵니다.
from urllib.parse import quote
# FastAPI 서버와 HTTP 통신하기 위해 requests를 가져옵니다.
import requests
# Django 설정에서 FastAPI 주소와 timeout 값을 읽기 위해 settings를 가져옵니다.
from django.conf import settings
# 사용자 안내 메시지를 출력하기 위해 messages를 가져옵니다.
from django.contrib import messages
# 로그인 사용자에게만 AI 기능을 허용하기 위해 login_required를 가져옵니다.
from django.contrib.auth.decorators import login_required
# JSON API 응답과 파일 스트리밍 응답을 만들기 위한 클래스를 가져옵니다.
from django.http import HttpResponse, JsonResponse
# HTML 화면 렌더링을 위해 render를 가져옵니다.
from django.shortcuts import render
# RAG 질문 폼을 가져옵니다.
from .forms import RagQueryForm


def _fastapi_url(path: str) -> str:
    """환경설정의 FastAPI 기본 주소와 API 경로를 안전하게 연결합니다."""
    # 끝 슬래시와 시작 슬래시를 정규화하여 이중 슬래시를 방지합니다.
    return f"{settings.FASTAPI_BASE_URL.rstrip('/')}/{path.lstrip('/')}"


def _error_message(response: requests.Response) -> str:
    """FastAPI 오류 응답에서 사용자가 이해할 detail 문자열을 추출합니다."""
    try:
        # FastAPI의 일반적인 {detail: ...} JSON 형식을 먼저 확인합니다.
        payload = response.json()
        # detail이 있으면 문자열로 변환해 반환합니다.
        return str(payload.get("detail") or payload)
    except ValueError:
        # JSON이 아니면 응답 본문의 앞부분을 오류 설명으로 사용합니다.
        return response.text[:1000] or f"HTTP {response.status_code}"


def _post_json(path: str, payload: dict) -> dict:
    """Django 서버가 FastAPI에 JSON POST를 보내고 성공 JSON을 반환합니다."""
    # 서버 간 통신이 무한정 대기하지 않도록 timeout을 적용합니다.
    response = requests.post(_fastapi_url(path), json=payload, timeout=settings.FASTAPI_REQUEST_TIMEOUT)
    # 4xx/5xx이면 FastAPI detail을 포함한 예외를 발생시킵니다.
    if not response.ok:
        raise RuntimeError(_error_message(response))
    # 정상 JSON을 파이썬 딕셔너리로 반환합니다.
    return response.json()


def _post_form(path: str, data: dict | None = None, files: dict | None = None) -> dict:
    """폼 또는 multipart 파일을 FastAPI로 전달하는 공통 프록시 함수입니다."""
    # Django가 받은 폼/파일을 FastAPI에 같은 이름으로 전송합니다.
    response = requests.post(_fastapi_url(path), data=data or {}, files=files or {}, timeout=settings.FASTAPI_AI_TIMEOUT)
    # FastAPI 오류는 Django JSON 오류로 변환할 수 있도록 예외 처리합니다.
    if not response.ok:
        raise RuntimeError(_error_message(response))
    # 성공 JSON 결과를 반환합니다.
    return response.json()


@login_required
def rag_search(request):
    """기존 Django RAG 화면을 유지하면서 실제 RAG 계산은 FastAPI에 위임합니다."""
    # POST 요청이면 입력값을 바인딩하고 GET이면 빈 폼을 생성합니다.
    form = RagQueryForm(request.POST or None)
    # 템플릿에 전달할 기본 답변과 검색 결과를 초기화합니다.
    answer = None
    results = []
    sync_result = None
    # 사용자가 유효한 질문을 제출했을 때만 FastAPI를 호출합니다.
    if request.method == "POST" and form.is_valid():
        try:
            # Django의 검증된 폼 값을 FastAPI RAG JSON 형식으로 구성합니다.
            payload = {
                "question": form.cleaned_data["question"],
                "source_scope": form.cleaned_data["source_scope"],
                "top_k": form.cleaned_data["top_k"],
                "sync_before_search": True,
            }
            # 실제 임베딩, ChromaDB 검색, LLM 답변은 FastAPI가 처리합니다.
            data = _post_json("/api/rag/query", payload)
            # FastAPI가 반환한 최종 답변을 화면 변수에 저장합니다.
            answer = data.get("answer")
            # 증분 색인 처리 결과를 화면 변수에 저장합니다.
            sync_result = data.get("sync_result")
            # 근거 결과를 순회하며 Django 원문 링크를 추가합니다.
            for result in data.get("results", []):
                # 메타데이터 딕셔너리를 읽습니다.
                metadata = result.get("metadata", {})
                # PDF 근거는 Django의 문서 프록시 URL로 연결합니다.
                if metadata.get("source_type") == "document":
                    metadata["url"] = f"/rag/documents/{quote(str(metadata.get('filename', '')))}"
                # 게시글 근거는 기존 Django 게시글 상세 URL을 그대로 사용합니다.
                elif metadata.get("source_type") == "board":
                    metadata["url"] = f"/boards/{metadata.get('board_id')}/"
                # 수정한 메타데이터를 검색 결과에 다시 저장합니다.
                result["metadata"] = metadata
                # 템플릿이 기존 객체 속성처럼 접근할 수 있도록 dict 결과를 추가합니다.
                results.append(result)
        except requests.RequestException as exc:
            # FastAPI 서버가 꺼져 있거나 네트워크 연결이 실패한 경우 안내합니다.
            messages.error(request, f"FastAPI AI 서버 연결 실패: {exc}")
        except Exception as exc:
            # FastAPI가 반환한 RAG 처리 오류를 화면에 표시합니다.
            messages.error(request, f"RAG 처리 중 오류가 발생했습니다: {exc}")
    # 기존 RAG 템플릿을 렌더링하여 Django 프론트 구조를 유지합니다.
    return render(request, "rag/search.html", {"form": form, "answer": answer, "results": results, "sync_result": sync_result})


@login_required
def rag_search_api(request):
    """기존 GET 방식 Django RAG API도 FastAPI 검색/답변 API와 연결해 호환성을 유지합니다."""
    # URL의 q 질문 파라미터를 읽고 공백을 제거합니다.
    question = request.GET.get("q", "").strip()
    # 검색 범위를 읽으며 기본값은 전체입니다.
    scope = request.GET.get("scope", "all")
    try:
        # top_k를 정수로 변환하고 1~10 범위로 제한합니다.
        top_k = max(1, min(int(request.GET.get("top_k", "5")), 10))
    except ValueError:
        # 잘못된 숫자 입력은 기본값 5를 사용합니다.
        top_k = 5
    # 질문이 비어 있으면 FastAPI를 호출하지 않습니다.
    if not question:
        return JsonResponse({"error": "q 질문 파라미터가 필요합니다."}, status=400)
    try:
        # FastAPI의 통합 query API를 호출합니다.
        data = _post_json("/api/rag/query", {"question": question, "source_scope": scope, "top_k": top_k, "sync_before_search": True})
        # 한글을 유니코드 이스케이프 없이 JSON으로 반환합니다.
        return JsonResponse(data, json_dumps_params={"ensure_ascii": False})
    except Exception as exc:
        # 서버 간 오류를 502 Bad Gateway 의미로 반환합니다.
        return JsonResponse({"error": str(exc)}, status=502, json_dumps_params={"ensure_ascii": False})


@login_required
def rag_document(request, filename):
    """FastAPI docs에 있는 근거 PDF를 Django 동일 출처로 프록시하여 표시합니다."""
    try:
        # 경로 구분자가 들어가지 않도록 파일명만 URL 인코딩해 FastAPI에 요청합니다.
        response = requests.get(_fastapi_url(f"/api/rag/documents/{quote(filename)}"), timeout=settings.FASTAPI_REQUEST_TIMEOUT)
        # PDF가 없거나 요청이 잘못되었으면 오류를 발생시킵니다.
        if not response.ok:
            return HttpResponse(_error_message(response), status=response.status_code, content_type="text/plain; charset=utf-8")
        # FastAPI에서 받은 PDF 바이트를 Django 응답으로 그대로 반환합니다.
        return HttpResponse(response.content, content_type="application/pdf")
    except requests.RequestException as exc:
        # FastAPI 연결 실패를 502로 명확하게 반환합니다.
        return HttpResponse(f"FastAPI 문서 서버 연결 실패: {exc}", status=502, content_type="text/plain; charset=utf-8")


@login_required
def multimodal_page(request):
    """Django 프론트에서 FastAPI 멀티모달 AI 기능을 사용하는 통합 화면입니다."""
    # 모든 AI API는 같은 Django origin으로 호출되도록 전용 템플릿을 렌더링합니다.
    return render(request, "rag/multimodal.html")


@login_required
def ai_health(request):
    """FastAPI 서버와 공유 MySQL 연결 상태를 Django에서 확인합니다."""
    try:
        # FastAPI health API를 서버 간 GET으로 호출합니다.
        response = requests.get(_fastapi_url("/api/health"), timeout=settings.FASTAPI_REQUEST_TIMEOUT)
        # FastAPI 오류가 있으면 예외를 발생시킵니다.
        if not response.ok:
            raise RuntimeError(_error_message(response))
        # FastAPI JSON을 Django JSON으로 그대로 반환합니다.
        return JsonResponse(response.json(), json_dumps_params={"ensure_ascii": False})
    except Exception as exc:
        # 프록시 실패는 502 상태로 반환합니다.
        return JsonResponse({"status": "error", "detail": str(exc)}, status=502, json_dumps_params={"ensure_ascii": False})


@login_required
def ai_caption(request):
    """Django에 업로드된 이미지를 FastAPI 캡셔닝 API로 전달합니다."""
    # POST 외 요청은 허용하지 않습니다.
    if request.method != "POST":
        return JsonResponse({"detail": "POST 요청만 허용됩니다."}, status=405)
    # HTML 파일 입력의 이름은 file로 통일합니다.
    uploaded = request.FILES.get("file")
    # 파일이 없으면 즉시 400을 반환합니다.
    if not uploaded:
        return JsonResponse({"detail": "이미지 파일이 필요합니다."}, status=400)
    try:
        # requests multipart 형식의 (파일명, 파일객체, MIME)을 구성합니다.
        files = {"file": (uploaded.name, uploaded.file, uploaded.content_type or "application/octet-stream")}
        # FastAPI 캡셔닝 결과를 받아 반환합니다.
        return JsonResponse(_post_form("/api/caption", files=files), json_dumps_params={"ensure_ascii": False})
    except Exception as exc:
        # AI 처리 실패를 502로 반환합니다.
        return JsonResponse({"detail": str(exc)}, status=502, json_dumps_params={"ensure_ascii": False})


@login_required
def ai_generate(request):
    """Django 프롬프트를 FastAPI Stable Diffusion 이미지 생성 API로 전달합니다."""
    # POST 외 요청은 거부합니다.
    if request.method != "POST":
        return JsonResponse({"detail": "POST 요청만 허용됩니다."}, status=405)
    try:
        # 브라우저가 보낸 이미지 생성 폼 값을 FastAPI가 기대하는 이름으로 전달합니다.
        data = {key: request.POST.get(key, "") for key in ("prompt", "negative_prompt", "steps", "guidance_scale", "seed")}
        # 빈 seed는 FastAPI에서 None 기본값을 쓰도록 전송 항목에서 제거합니다.
        data = {key: value for key, value in data.items() if value != ""}
        # FastAPI 이미지 생성 API를 호출합니다.
        result = _post_form("/api/generate", data=data)
        # 상대 이미지 URL이면 FastAPI 서버의 절대 URL로 변환하여 Django 페이지의 img 태그가 읽을 수 있게 합니다.
        if result.get("image_url", "").startswith("/"):
            result["image_url"] = _fastapi_url(result["image_url"])
        # 생성 결과 JSON을 반환합니다.
        return JsonResponse(result, json_dumps_params={"ensure_ascii": False})
    except Exception as exc:
        # 모델 처리 실패를 502로 반환합니다.
        return JsonResponse({"detail": str(exc)}, status=502, json_dumps_params={"ensure_ascii": False})


@login_required
def ai_stt(request):
    """브라우저에서 녹음한 WAV를 FastAPI Whisper STT API로 전달합니다."""
    # POST 외 요청은 허용하지 않습니다.
    if request.method != "POST":
        return JsonResponse({"detail": "POST 요청만 허용됩니다."}, status=405)
    # WAV 업로드 파일을 가져옵니다.
    uploaded = request.FILES.get("file")
    # 파일이 없으면 400을 반환합니다.
    if not uploaded:
        return JsonResponse({"detail": "WAV 음성 파일이 필요합니다."}, status=400)
    try:
        # FastAPI 파일 업로드 형식으로 변환합니다.
        files = {"file": (uploaded.name, uploaded.file, uploaded.content_type or "audio/wav")}
        # Whisper STT 결과를 반환합니다.
        return JsonResponse(_post_form("/api/stt", files=files), json_dumps_params={"ensure_ascii": False})
    except Exception as exc:
        # STT 실패를 502로 반환합니다.
        return JsonResponse({"detail": str(exc)}, status=502, json_dumps_params={"ensure_ascii": False})


@login_required
def ai_tts(request):
    """Django의 텍스트를 FastAPI TTS API로 전달합니다."""
    # POST 외 요청은 허용하지 않습니다.
    if request.method != "POST":
        return JsonResponse({"detail": "POST 요청만 허용됩니다."}, status=405)
    try:
        # 입력 텍스트를 FastAPI 폼 값으로 전달합니다.
        result = _post_form("/api/tts", data={"text": request.POST.get("text", "")})
        # 상대 오디오 URL이면 FastAPI 절대 URL로 변환합니다.
        if result.get("audio_url", "").startswith("/"):
            result["audio_url"] = _fastapi_url(result["audio_url"])
        # TTS 결과를 JSON으로 반환합니다.
        return JsonResponse(result, json_dumps_params={"ensure_ascii": False})
    except Exception as exc:
        # TTS 처리 실패를 502로 반환합니다.
        return JsonResponse({"detail": str(exc)}, status=502, json_dumps_params={"ensure_ascii": False})
