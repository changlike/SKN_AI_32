from django import forms
from .models import Board

class BoardForm(forms.ModelForm):
    """게시글 작성 및 수정 Form 입니다."""
    class Meta:
        # 사용할 Model 지정
        model = Board

        # 사용자로부터 입력받을 필드만 지정함
        # author는 로그인한 사용자 정보에서 꺼내서 사용할 것임
        fields = ("title", "content", "attachment")

        widgets = {
            # 본문은 textarea로 출력함
            "content": forms.Textarea(attrs={"rows": 10}),
        }
    # class Meta -----------------------------------------

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # 모든 Form 요소에 CSS 적용함
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")

# class --------------------------------------------------------------


