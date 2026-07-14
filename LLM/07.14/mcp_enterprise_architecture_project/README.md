# MCP 실무 아키텍처 프로젝트

## 아키텍처

```text
사용자
  ↓
FastAPI
  ↓
OpenAI
  ↓
MCP Client
  ↓ stdio / JSON-RPC
MCP Server
  ├── File Tool
  ├── DB Tool
  ├── GitHub Tool
  ├── Slack Tool
  ├── Browser Tool
  ├── Calendar Tool
  ├── Email Tool
  ├── Vector Search Tool
  └── Python 실행 Tool
  ↓
외부 시스템(메모리 바깥 all) 
```

이 프로젝트는 PyCharm에서 각 계층의 역할을 직접 실행하고 확인할 수 있도록 구성했습니다.

## Tool 구성

| 범주 | MCP Tool |
|---|---|
| File | `file_list`, `file_read`, `file_write` |
| DB | `db_add_note`, `db_list_notes`, `db_search_notes` |
| GitHub | `github_list_issues`, `github_create_issue` |
| Slack | `slack_post_message` |
| Browser | `browser_fetch_text` |
| Calendar | `calendar_create_event`, `calendar_list_events` |
| Email | `email_send` |
| Vector Search | `vector_rebuild_index`, `vector_search` |
| Python | `python_calculate` |

## 안전한 기본 동작

- `LIVE_MODE=false`에서는 GitHub, Slack, Email이 데모 결과를 반환합니다.
- File Tool은 `data/files` 폴더 밖에 접근할 수 없습니다.
- Browser Tool은 `.env`의 허용 호스트에만 접근합니다.
- DB Tool은 임의 SQL을 실행하지 않고 업무 메모 기능만 제공합니다.
- Python Tool은 임의 코드를 실행하지 않고 산술 표현식만 처리합니다.
- Calendar Tool은 로컬 JSON 파일을 사용합니다.
- Vector Search는 외부 모델 없이 TF-IDF 방식으로 작동합니다.

## 1. PyCharm에서 프로젝트 열기

압축을 해제한 뒤 `mcp_enterprise_architecture_project` 폴더를 엽니다.

Python 3.11 가상환경을 권장합니다.

## 2. 패키지 설치

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
Copy-Item .env.example .env
```

## 3. FastAPI 실행

```powershell
python -m app.main
```

접속 주소:

- 웹 UI: `http://127.0.0.1:8000`
- Swagger: `http://127.0.0.1:8000/docs`
- 상태: `http://127.0.0.1:8000/api/health`

## 4. MCP Server만 실행

```powershell
python -m mcp_server.server
```

stdio 서버는 화면을 제공하지 않고 MCP Client의 연결을 기다립니다.

## 5. MCP Inspector 실행

Node.js가 설치되어 있다면 다음 명령을 실행합니다.

```powershell
npx -y @modelcontextprotocol/inspector python -m mcp_server.server
```

## 6. 웹 UI에서 Tool 직접 호출

### Python 계산

Tool 이름:

```text
python_calculate
```

인수:

```json
{
  "expression": "(12 + 8) * 3"
}
```

### 파일 목록

```text
file_list
```

```json
{}
```

### 업무 메모 등록

```text
db_add_note
```

```json
{
  "title": "MCP 회의",
  "content": "금요일까지 Tool 연동을 완료한다."
}
```

### Vector 인덱스 생성

```text
vector_rebuild_index
```

```json
{}
```

### Vector 검색

```text
vector_search
```

```json
{
  "query": "MCP Tool 보안 원칙",
  "top_k": 2
}
```

### 일정 등록

```text
calendar_create_event
```

```json
{
  "title": "MCP 프로젝트 회의",
  "start": "2026-07-15T14:00:00",
  "end": "2026-07-15T15:00:00",
  "description": "Tool 통합 상태 점검"
}
```

## 7. OpenAI + MCP 자동 Tool 선택

`.env`에 API 키를 설정합니다.

```env
OPENAI_API_KEY=발급받은_OpenAI_API_KEY
OPENAI_MODEL=gpt-4.1-mini
```

FastAPI를 다시 시작한 뒤 웹 UI의 `OpenAI + MCP Assistant`에서 자연어로 요청합니다.

```text
업무 문서 목록을 확인해줘.
```

OpenAI는 MCP Server에서 받은 Tool 스키마를 보고 필요한 Tool을 선택합니다. FastAPI 내부의 MCP Client가 stdio로 MCP Server를 실행하고 Tool 결과를 OpenAI에 다시 전달합니다.

## 8. 실제 GitHub, Slack, Email 연결

`.env`에서 다음 값을 설정합니다.

```env
LIVE_MODE=true

GITHUB_TOKEN=...
GITHUB_OWNER=...
GITHUB_REPO=...

SLACK_BOT_TOKEN=...
SLACK_CHANNEL_ID=...

SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=...
SMTP_PASSWORD=...
EMAIL_FROM=...
```

`LIVE_MODE=true`에서는 외부 시스템이 실제로 변경될 수 있으므로 테스트 저장소와 테스트 채널을 먼저 사용해야 합니다.

## 9. 테스트

```powershell
pytest -q
```

## 10. 주요 API

| Method | URL | 설명 |
|---|---|---|
| GET | `/api/health` | 서버 상태 |
| GET | `/api/mcp/tools` | MCP Tool 목록 |
| POST | `/api/mcp/call` | MCP Tool 직접 호출 |
| POST | `/api/assistant` | OpenAI + MCP Assistant |
