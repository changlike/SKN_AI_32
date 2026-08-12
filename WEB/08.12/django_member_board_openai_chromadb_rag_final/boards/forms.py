"""게시글 등록과 수정에 공통으로 사용할 ModelForm입니다."""
# Django 폼 모듈을 가져옵니다.
from django import forms
# Board ORM 모델을 가져옵니다.
from .models import Board


class BoardForm(forms.ModelForm):
    """작성자는 서버의 request.user로 지정하고 제목/내용/파일만 입력받습니다."""
    class Meta:
        # 저장 대상 모델을 Board로 지정합니다.
        model = Board
        # 사용자가 직접 수정 가능한 필드만 폼에 노출합니다.
        fields = ("title", "content", "attachment")
        # 내용 입력칸은 여러 줄 textarea로 표시합니다.
        widgets = {"content": forms.Textarea(attrs={"rows": 10})}

    def __init__(self, *args, **kwargs):
        """각 입력 요소에 공통 CSS 클래스를 적용합니다."""
        # ModelForm 기본 초기화를 수행합니다.
        super().__init__(*args, **kwargs)
        # 모든 폼 필드 위젯에 form-control 스타일을 적용합니다.
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")
