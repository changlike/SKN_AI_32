"""React → Django → FastAPI 구조를 위한 AI/RAG JSON 프록시 API입니다.
기존 rag.views의 FastAPI 호출 함수와 동일한 서비스 엔드포인트를 재사용합니다.
"""
from urllib.parse import quote
import requests
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views import View

from api.helpers import JsonLoginRequiredMixin, json_error
from .forms import RagQueryForm
from .views import _error_message, _fastapi_url, _post_form, _post_json


class RagQueryAPIView(JsonLoginRequiredMixin, View):
    def get(self, request):
        question = request.GET.get("q", "").strip()
        scope = request.GET.get("scope", "all")
        try:
            top_k = max(1, min(int(request.GET.get("top_k", "5")), 10))
        except ValueError:
            top_k = 5
        if not question:
            return json_error("q 질문 파라미터가 필요합니다.", 400)
        return self._query(question, scope, top_k)

    def post(self, request):
        form = RagQueryForm(request.POST)
        if not form.is_valid():
            from api.helpers import form_errors
            return json_error("RAG 질문 입력값을 확인하세요.", 400, form_errors(form))
        return self._query(form.cleaned_data["question"], form.cleaned_data["source_scope"], form.cleaned_data["top_k"])

    def _query(self, question, scope, top_k):
        try:
            data = _post_json("/api/rag/query", {
                "question": question,
                "source_scope": scope,
                "top_k": top_k,
                "sync_before_search": True,
            })
            for result in data.get("results", []):
                metadata = result.get("metadata") or {}
                if metadata.get("source_type") == "document":
                    metadata["url"] = f"/api/ai/documents/{quote(str(metadata.get('filename', '')))}/"
                elif metadata.get("source_type") == "board":
                    metadata["url"] = f"/boards/{metadata.get('board_id')}"
                result["metadata"] = metadata
            data["ok"] = True
            return JsonResponse(data, json_dumps_params={"ensure_ascii": False})
        except Exception as exc:
            return json_error(str(exc), 502)


class RagDocumentAPIView(JsonLoginRequiredMixin, View):
    def get(self, request, filename):
        try:
            response = requests.get(_fastapi_url(f"/api/rag/documents/{quote(filename)}"), timeout=settings.FASTAPI_REQUEST_TIMEOUT)
            if not response.ok:
                return HttpResponse(_error_message(response), status=response.status_code, content_type="text/plain; charset=utf-8")
            return HttpResponse(response.content, content_type="application/pdf")
        except requests.RequestException as exc:
            return HttpResponse(f"FastAPI 문서 서버 연결 실패: {exc}", status=502, content_type="text/plain; charset=utf-8")


class AIHealthAPIView(JsonLoginRequiredMixin, View):
    def get(self, request):
        try:
            response = requests.get(_fastapi_url("/api/health"), timeout=settings.FASTAPI_REQUEST_TIMEOUT)
            if not response.ok:
                raise RuntimeError(_error_message(response))
            data = response.json()
            data["ok"] = True
            return JsonResponse(data, json_dumps_params={"ensure_ascii": False})
        except Exception as exc:
            return json_error(str(exc), 502)


class FastAPIMediaProxyAPIView(JsonLoginRequiredMixin, View):
    """FastAPI 생성 이미지/TTS 음원을 Django를 통해 스트리밍하여 브라우저의 FastAPI 직접 접근을 막습니다."""
    def get(self, request, asset_path):
        try:
            response = requests.get(_fastapi_url(f"/media/{asset_path}"), timeout=settings.FASTAPI_AI_TIMEOUT, stream=True)
            if not response.ok:
                return HttpResponse(_error_message(response), status=response.status_code, content_type="text/plain; charset=utf-8")
            content_type = response.headers.get("Content-Type", "application/octet-stream")
            return HttpResponse(response.content, content_type=content_type)
        except requests.RequestException as exc:
            return HttpResponse(f"FastAPI 미디어 서버 연결 실패: {exc}", status=502, content_type="text/plain; charset=utf-8")


class AICaptionAPIView(JsonLoginRequiredMixin, View):
    def post(self, request):
        uploaded = request.FILES.get("file")
        if not uploaded:
            return json_error("이미지 파일이 필요합니다.", 400)
        try:
            files = {"file": (uploaded.name, uploaded.file, uploaded.content_type or "application/octet-stream")}
            data = _post_form("/api/caption", files=files)
            data["ok"] = True
            return JsonResponse(data, json_dumps_params={"ensure_ascii": False})
        except Exception as exc:
            return json_error(str(exc), 502)


class AIGenerateAPIView(JsonLoginRequiredMixin, View):
    def post(self, request):
        try:
            data = {key: request.POST.get(key, "") for key in ("prompt", "negative_prompt", "steps", "guidance_scale", "seed")}
            data = {key: value for key, value in data.items() if value != ""}
            result = _post_form("/api/generate", data=data)
            if result.get("image_url", "").startswith("/"):
                result["image_url"] = f"/api/ai/media/{result['image_url'].removeprefix('/media/')}/"
            result["ok"] = True
            return JsonResponse(result, json_dumps_params={"ensure_ascii": False})
        except Exception as exc:
            return json_error(str(exc), 502)


class AISTTAPIView(JsonLoginRequiredMixin, View):
    def post(self, request):
        uploaded = request.FILES.get("file")
        if not uploaded:
            return json_error("WAV 음성 파일이 필요합니다.", 400)
        try:
            files = {"file": (uploaded.name, uploaded.file, uploaded.content_type or "audio/wav")}
            data = _post_form("/api/stt", files=files)
            data["ok"] = True
            return JsonResponse(data, json_dumps_params={"ensure_ascii": False})
        except Exception as exc:
            return json_error(str(exc), 502)


class AITTSAPIView(JsonLoginRequiredMixin, View):
    def post(self, request):
        try:
            result = _post_form("/api/tts", data={"text": request.POST.get("text", "")})
            if result.get("audio_url", "").startswith("/"):
                result["audio_url"] = f"/api/ai/media/{result['audio_url'].removeprefix('/media/')}/"
            result["ok"] = True
            return JsonResponse(result, json_dumps_params={"ensure_ascii": False})
        except Exception as exc:
            return json_error(str(exc), 502)
