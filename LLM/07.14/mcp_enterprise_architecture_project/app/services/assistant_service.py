"""
사용자 질문을 OpenAI에 전달하고 MCP Tool 호출을 연결하는 Assistant 서비스입니다.
"""

# JSON 문자열을 처리하기 위해 json을 가져옵니다.
import json

# OpenAI 클라이언트를 가져옵니다.
from openai import OpenAI

# 설정을 가져옵니다.
from app.core.settings import get_settings

# MCP Client 서비스를 가져옵니다.
from mcp_client.client import MCPClientService


# Assistant 서비스를 정의합니다.
class AssistantService:
    """OpenAI가 선택한 MCP Tool을 실행하고 최종 답변을 생성합니다."""

    # 필요한 클라이언트를 초기화합니다.
    def __init__(self) -> None:
        # 설정을 가져옵니다.
        self.settings = get_settings()

        # MCP Client 서비스를 생성합니다.
        self.mcp_client = MCPClientService()

        # OpenAI API 키가 있을 때만 클라이언트를 생성합니다.
        self.openai = (
            OpenAI(api_key=self.settings.openai_api_key)
            if self.settings.openai_api_key
            else None
        )

    # MCP Tool 목록을 OpenAI 함수 Tool 형식으로 변환합니다.
    async def _openai_tools(self) -> list[dict]:
        """MCP Tool 스키마를 OpenAI Responses API Tool 형식으로 변환합니다."""

        # MCP 서버에서 Tool 목록을 읽습니다.
        tools = await self.mcp_client.list_tools()

        # OpenAI 함수 Tool 정의 목록으로 변환합니다.
        return [
            {
                "type": "function",
                "name": item["name"],
                "description": item["description"] or "",
                "parameters": item["inputSchema"],
                "strict": False,
            }
            for item in tools
        ]

    # 사용자 질문을 처리합니다.
    async def ask(self, message: str) -> dict:
        """OpenAI와 MCP Tool을 연결하여 답변을 생성합니다."""

        # API 키가 없으면 사용 가능한 Tool 안내를 반환합니다.
        if self.openai is None:
            tools = await self.mcp_client.list_tools()
            return {
                "mode": "local",
                "answer": (
                    "OPENAI_API_KEY가 설정되지 않아 자동 Tool 선택은 생략했습니다. "
                    "아래 Tool 목록에서 원하는 Tool을 /api/mcp/call로 직접 실행할 수 있습니다."
                ),
                "tools": [tool["name"] for tool in tools],
            }

        # MCP Tool 목록을 OpenAI Tool 형식으로 변환합니다.
        tools = await self._openai_tools()

        # 최초 사용자 요청을 Responses API에 전달합니다.
        response = self.openai.responses.create(
            model=self.settings.openai_model,
            instructions=(
                "당신은 MCP 기반 업무 Assistant입니다. "
                "필요할 때만 Tool을 사용하고 Tool 결과를 근거로 한국어로 답하세요. "
                "외부 변경 작업은 사용자가 명확히 요청한 경우에만 수행하세요."
            ),
            input=message,
            tools=tools,
        )

        # 실행된 Tool 기록을 저장합니다.
        tool_trace: list[dict] = []

        # 모델이 반환한 함수 호출 항목을 추출합니다.
        function_calls = [item for item in response.output if item.type == "function_call"]

        # Tool 호출이 없으면 생성된 텍스트를 그대로 반환합니다.
        if not function_calls:
            return {"mode": "openai", "answer": response.output_text, "tool_trace": tool_trace}

        # 후속 입력으로 전달할 Tool 결과 목록을 생성합니다.
        tool_outputs: list[dict] = []

        # 각 함수 호출을 순서대로 처리합니다.
        for call in function_calls:
            # JSON 문자열 인수를 Python 딕셔너리로 변환합니다.
            arguments = json.loads(call.arguments or "{}")

            # MCP Client를 통해 실제 MCP Tool을 호출합니다.
            result = await self.mcp_client.call_tool(call.name, arguments)

            # 실행 추적 정보를 저장합니다.
            tool_trace.append({"tool": call.name, "arguments": arguments, "result": result})

            # OpenAI에 반환할 함수 결과 항목을 구성합니다.
            tool_outputs.append(
                {
                    "type": "function_call_output",
                    "call_id": call.call_id,
                    "output": json.dumps(result, ensure_ascii=False),
                }
            )

        # 이전 응답에 Tool 결과를 연결하여 최종 답변 생성을 요청합니다.
        final_response = self.openai.responses.create(
            model=self.settings.openai_model,
            previous_response_id=response.id,
            input=tool_outputs,
            tools=tools,
        )

        # 최종 답변과 Tool 실행 기록을 반환합니다.
        return {
            "mode": "openai",
            "answer": final_response.output_text,
            "tool_trace": tool_trace,
        }
