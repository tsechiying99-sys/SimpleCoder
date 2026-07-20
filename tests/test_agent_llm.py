"""Tests for Agent orchestration and LLM response data structures."""

from simplecoder.agent import Agent
from simplecoder.llm import LLMResponse, ToolCall
from simplecoder.tools.base import Tool


class EchoTool(Tool):
    name = "echo_tool"
    description = "Return the given text."
    parameters = {
        "type": "object",
        "properties": {"text": {"type": "string"}},
        "required": ["text"],
    }

    def execute(self, text: str) -> str:
        return f"echo: {text}"


class FakeLLM:
    model = "fake-model"
    total_prompt_tokens = 0
    total_completion_tokens = 0

    @property
    def estimated_cost(self):
        return None

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def chat(self, messages, tools=None, on_token=None):
        self.calls.append({"messages": messages, "tools": tools})
        response = self.responses.pop(0)
        if on_token and response.content:
            on_token(response.content)
        return response


def test_llm_response_message_with_tool_calls():
    response = LLMResponse(
        content="",
        tool_calls=[ToolCall(id="call-1", name="read_file", arguments={"file_path": "x.py"})],
    )

    message = response.message

    assert message["role"] == "assistant"
    assert message["tool_calls"][0]["id"] == "call-1"
    assert '"file_path": "x.py"' in message["tool_calls"][0]["function"]["arguments"]


def test_agent_returns_plain_text_without_tools():
    llm = FakeLLM([LLMResponse(content="done")])
    agent = Agent(llm=llm, tools=[])

    result = agent.chat("hello")

    assert result == "done"
    assert agent.messages[-1]["role"] == "assistant"


def test_agent_passes_tool_schemas_to_llm():
    llm = FakeLLM([LLMResponse(content="done")])
    agent = Agent(llm=llm, tools=[EchoTool()])

    agent.chat("hello")

    assert llm.calls[0]["tools"][0]["function"]["name"] == "echo_tool"


def test_agent_records_tool_result_with_openai_tool_role():
    llm = FakeLLM([
        LLMResponse(
            tool_calls=[ToolCall(id="call-1", name="echo_tool", arguments={"text": "hello"})],
        ),
        LLMResponse(content="finished"),
    ])
    agent = Agent(llm=llm, tools=[EchoTool()])

    result = agent.chat("use the tool")

    assert result == "finished"
    tool_messages = [m for m in agent.messages if m.get("tool_call_id") == "call-1"]
    assert tool_messages == [
        {"role": "tool", "tool_call_id": "call-1", "content": "echo: hello"}
    ]


def test_exec_tool_distinguishes_bad_arguments_from_internal_type_error():
    class BoomTool(Tool):
        name = "boom"
        description = "Raise TypeError internally."
        parameters = {"type": "object", "properties": {}, "required": []}

        def execute(self):
            raise TypeError("internal explosion")

    agent = Agent(llm=FakeLLM([]), tools=[BoomTool()])

    class BadArgs:
        name = "boom"
        id = "bad"
        arguments = {"unexpected": 1}

    class GoodArgs:
        name = "boom"
        id = "good"
        arguments = {}

    assert "bad arguments" in agent._exec_tool(BadArgs())
    assert "Error executing boom" in agent._exec_tool(GoodArgs())
