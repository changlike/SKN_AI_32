"""RAG 검색 화면, 검색 API, 근거 PDF 제공 View입니다."""
from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import render
from django.urls import reverse

from .forms import RagQueryForm
from .service import RagService


@login_required
def rag_search(request):
    """질문을 받아 벡터 검색 후 OpenAI가 근거 기반 답변을 생성합니다."""
    form = RagQueryForm(request.POST or None)
    answer = None
    results = []
    sync_result = None

    if request.method == "POST" and form.is_valid():
        try:
            service = RagService()
            # 새 PDF와 게시글 변경분이 있으면 질문 전에 자동으로 증분 반영합니다.
            sync_result = service.sync_all(force=False)
            results = service.search(
                form.cleaned_data["question"],
                source_scope=form.cleaned_data["source_scope"],
                top_k=form.cleaned_data["top_k"],
            )
            answer = service.answer(form.cleaned_data["question"], results)

            # 템플릿에서 바로 사용할 수 있도록 근거 링크를 메타데이터에 추가합니다.
            for result in results:
                if result.metadata.get("source_type") == "document":
                    result.metadata["url"] = reverse(
                        "rag:document",
                        kwargs={"filename": result.metadata.get("filename", "")},
                    )
                elif result.metadata.get("source_type") == "board":
                    result.metadata["url"] = reverse(
                        "boards:detail",
                        kwargs={"pk": result.metadata.get("board_id")},
                    )
        except Exception as exc:
            messages.error(request, f"RAG 처리 중 오류가 발생했습니다: {exc}")

    return render(
        request,
        "rag/search.html",
        {"form": form, "answer": answer, "results": results, "sync_result": sync_result},
    )


@login_required
def rag_search_api(request):
    """GET q 파라미터로 벡터 검색 결과를 JSON으로 반환합니다."""
    question = request.GET.get("q", "").strip()
    scope = request.GET.get("scope", "all")
    try:
        top_k = max(1, min(int(request.GET.get("top_k", "5")), 10))
    except ValueError:
        top_k = 5

    if not question:
        return JsonResponse({"error": "q 질문 파라미터가 필요합니다."}, status=400)
    if scope not in {"all", "documents", "boards"}:
        return JsonResponse({"error": "scope는 all, documents, boards 중 하나여야 합니다."}, status=400)

    try:
        service = RagService()
        service.sync_all(force=False)
        results = service.search(question, source_scope=scope, top_k=top_k)
        return JsonResponse(
            {
                "question": question,
                "scope": scope,
                "results": [
                    {
                        "text": result.text,
                        "similarity": result.similarity,
                        "metadata": result.metadata,
                    }
                    for result in results
                ],
            },
            json_dumps_params={"ensure_ascii": False},
        )
    except Exception as exc:
        return JsonResponse({"error": str(exc)}, status=500, json_dumps_params={"ensure_ascii": False})


@login_required
def rag_document(request, filename):
    """로그인 사용자에게 docs 폴더의 PDF 근거 문서를 안전하게 제공합니다."""
    docs_dir = Path(settings.RAG_DOCS_DIR).resolve()
    target = (docs_dir / filename).resolve()
    if docs_dir not in target.parents or not target.is_file() or target.suffix.lower() != ".pdf":
        raise Http404("문서를 찾을 수 없습니다.")
    return FileResponse(open(target, "rb"), content_type="application/pdf")
