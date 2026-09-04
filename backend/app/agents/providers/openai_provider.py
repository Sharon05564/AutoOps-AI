import json

from openai import AsyncOpenAI

from app.agents.json_utils import parse_diagnosis
from app.agents.prompts import SYSTEM_PROMPT, USER_PROMPT
from app.agents.providers.base import InvestigationProvider
from app.agents.schemas import Diagnosis
from app.tools.definitions import READ_ONLY_TOOLS
from app.tools.executor import ToolExecutor

MAX_TOOL_CALL_TURNS = 8


def _as_openai_tools() -> list[dict]:
    return [
        {
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["parameters"],
            },
        }
        for tool in READ_ONLY_TOOLS
    ]


class OpenAIProvider(InvestigationProvider):
    """Real tool-calling investigation loop against the OpenAI Chat Completions API.

    Requires OPENAI_API_KEY. The model only ever sees read-only tools - it
    cannot execute a rollback/restart/scale itself, it can only recommend one.
    """

    name = "openai"

    def __init__(self, api_key: str, model: str):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model

    async def investigate(self, executor: ToolExecutor) -> Diagnosis:
        tools = _as_openai_tools()
        messages: list[dict] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPT},
        ]

        for _ in range(MAX_TOOL_CALL_TURNS):
            response = await self.client.chat.completions.create(
                model=self.model, messages=messages, tools=tools, tool_choice="auto"
            )
            message = response.choices[0].message

            if message.tool_calls:
                messages.append(
                    {
                        "role": "assistant",
                        "content": message.content,
                        "tool_calls": [
                            {
                                "id": tc.id,
                                "type": "function",
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": tc.function.arguments,
                                },
                            }
                            for tc in message.tool_calls
                        ],
                    }
                )
                for tool_call in message.tool_calls:
                    arguments = json.loads(tool_call.function.arguments or "{}")
                    result = await executor.execute(tool_call.function.name, arguments)
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": json.dumps(result),
                        }
                    )
                continue

            return parse_diagnosis(message.content or "")

        raise RuntimeError(
            f"OpenAI investigation did not converge within {MAX_TOOL_CALL_TURNS} turns"
        )
