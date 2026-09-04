from anthropic import AsyncAnthropic

from app.agents.json_utils import parse_diagnosis
from app.agents.prompts import SYSTEM_PROMPT, USER_PROMPT
from app.agents.providers.base import InvestigationProvider
from app.agents.schemas import Diagnosis
from app.tools.definitions import READ_ONLY_TOOLS
from app.tools.executor import ToolExecutor

MAX_TOOL_CALL_TURNS = 8
MAX_TOKENS = 2048


def _as_anthropic_tools() -> list[dict]:
    return [
        {
            "name": tool["name"],
            "description": tool["description"],
            "input_schema": tool["parameters"],
        }
        for tool in READ_ONLY_TOOLS
    ]


class AnthropicProvider(InvestigationProvider):
    """Real tool-calling investigation loop against the Anthropic Messages API.

    Requires ANTHROPIC_API_KEY. Like the OpenAI provider, the model only ever
    sees read-only tools and can only recommend a remediation, never execute one.
    """

    name = "anthropic"

    def __init__(self, api_key: str, model: str):
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = model

    async def investigate(self, executor: ToolExecutor) -> Diagnosis:
        tools = _as_anthropic_tools()
        messages: list[dict] = [{"role": "user", "content": USER_PROMPT}]

        for _ in range(MAX_TOOL_CALL_TURNS):
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=MAX_TOKENS,
                system=SYSTEM_PROMPT,
                messages=messages,
                tools=tools,
            )

            messages.append({"role": "assistant", "content": response.content})

            tool_use_blocks = [block for block in response.content if block.type == "tool_use"]
            if response.stop_reason == "tool_use" and tool_use_blocks:
                tool_results = []
                for block in tool_use_blocks:
                    result = await executor.execute(block.name, block.input or {})
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": str(result),
                        }
                    )
                messages.append({"role": "user", "content": tool_results})
                continue

            text_blocks = [block.text for block in response.content if block.type == "text"]
            return parse_diagnosis("\n".join(text_blocks))

        raise RuntimeError(
            f"Anthropic investigation did not converge within {MAX_TOOL_CALL_TURNS} turns"
        )
