`django_web`의 각 앱 View를 **함수 기반 뷰(FBV)에서 클래스 기반 뷰(CBV)로 변경한 최종 프로젝트**

회원가입·로그인·로그아웃·회원정보 수정·회원탈퇴·관리자 회원관리, 게시판 검색·페이징·CRUD·조회수·권한 검사·첨부파일 처리, RAG 검색·FastAPI 연동·PDF 근거 문서·이미지 캡셔닝·이미지 생성·STT·TTS·Health API 기능을 그대로 유지했습니다.

주요 변경은 다음과 같습니다.

* `members/views.py`

  * `HomeView`
  * `SignUpView`
  * `LoginView`
  * `LogoutView`
  * `ProfileView`
  * `ProfileUpdateView`
  * `WithdrawView`
  * `MemberListView`
  * `ToggleActiveView`
* `boards/views.py`

  * `BoardListView`
  * `BoardDetailView`
  * `BoardCreateView`
  * `BoardUpdateView`
  * `BoardDeleteView`
* `rag/views.py`

  * `RagSearchView`
  * `RagSearchAPIView`
  * `RagDocumentView`
  * `MultimodalPageView`
  * `AIHealthView`
  * `AICaptionView`
  * `AIGenerateView`
  * `AISTTView`
  * `AITTSView`

로그인 제한은 `LoginRequiredMixin` 기반으로 변경했고, 관리자 권한 부분은 기존 `user_passes_test()`의 동작까지 유지하도록 클래스 `dispatch`에 적용했습니다. URL에서는 기존 경로와 `name`을 전혀 변경하지 않고 다음처럼 `as_view()`만 적용했습니다.

```python
path("login/", views.LoginView.as_view(), name="login")
path("", views.BoardListView.as_view(), name="list")
path("", views.RagSearchView.as_view(), name="search")
```

