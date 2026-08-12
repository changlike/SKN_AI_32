"""RAG 질문 입력과 검색 범위를 검증하는 폼입니다."""
from django import forms


class RagQueryForm(forms.Form):
    """사용자의 자연어 질문과 검색 범위를 입력받습니다."""

    SOURCE_CHOICES = [
        ("all", "전체: 문서 + 게시글"),
        ("documents", "근거 문서만"),
        ("boards", "게시글만"),
    ]

    question = forms.CharField(
        label="질문",
        max_length=1000,
        widget=forms.Textarea(
            attrs={
                "rows": 4,
                "placeholder": "예: 상품을 반품하려면 며칠 안에 신청해야 하나요?",
            }
        ),
    )
    source_scope = forms.ChoiceField(
        label="검색 범위",
        choices=SOURCE_CHOICES,
        initial="all",
    )
    top_k = forms.IntegerField(
        label="검색 문서 수",
        min_value=1,
        max_value=10,
        initial=5,
    )
