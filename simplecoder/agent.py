"""SimpleCoder 的核心 Agent 循环。

流程：
    用户消息 -> LLM（携带工具 schema）-> 模型是否请求调用工具？
                                      -> 是：执行工具，把结果发回 LLM，继续循环
                                      -> 否：返回最终文本回复

这个文件只负责“调度”：维护消息历史、把工具 schema 交给模型、
执行模型请求的工具调用，并在上下文过长时触发压缩。
"""

import concurrent.futures
import inspect

from .context import ContextManager
from .llm import LLM
from .prompt import system_prompt
from .tools import ALL_TOOLS
from .tools.agent import AgentTool
from .tools.base import Tool


class Agent:
    """一个最小可用的 Coding Agent。"""

    def __init__(
        self,
        llm: LLM,
        tools: list[Tool] | None = None,
        max_context_tokens: int = 128_000,
        max_rounds: int = 50,
    ):
        self.llm = llm
        self.tools = tools if tools is not None else ALL_TOOLS
        self._tool_by_name = {t.name: t for t in self.tools}
        self.messages: list[dict] = []
        self.context = ContextManager(max_tokens=max_context_tokens)
        self.max_rounds = max_rounds
        self._system = system_prompt(self.tools)

        # 子 Agent 工具需要知道父 Agent，才能复用同一个 LLM 配置。
        for t in self.tools:
            if isinstance(t, AgentTool):
                t._parent_agent = self

    def _full_messages(self) -> list[dict]:
        """拼出真正发给模型的消息：system prompt + 当前会话历史。"""
        return [{"role": "system", "content": self._system}] + self.messages

    def _tool_schemas(self) -> list[dict]:
        """把 Python 工具对象转换为 OpenAI-compatible function schema。"""
        return [t.schema() for t in self.tools]

    def chat(self, user_input: str, on_token=None, on_tool=None) -> str:
        """处理一条用户消息；中间可能经历多轮 LLM/工具调用。"""
        self.messages.append({"role": "user", "content": user_input})
        self.context.maybe_compress(self.messages, self.llm)

        for _ in range(self.max_rounds):
            resp = self.llm.chat(
                messages=self._full_messages(),
                tools=self._tool_schemas(),
                on_token=on_token,
            )

            # 没有工具调用，说明模型已经给出最终回答。
            if not resp.tool_calls:
                self.messages.append(resp.message)
                return resp.content

            # 有工具调用时，先保存 assistant 的 tool_calls 消息。
            self.messages.append(resp.message)

            try:
                if len(resp.tool_calls) == 1:
                    tc = resp.tool_calls[0]
                    if on_tool:
                        on_tool(tc.name, tc.arguments)
                    result = self._exec_tool(tc)
                    self.messages.append({
                        "role": "tools",
                        "tool_call_id": tc.id,
                        "content": result,
                    })
                else:
                    # 多个工具调用可以并行执行，节省等待时间。
                    results = self._exec_tools_parallel(resp.tool_calls, on_tool)
                    for tc, result in zip(resp.tool_calls, results):
                        self.messages.append({
                            "role": "tools",
                            "tool_call_id": tc.id,
                            "content": result,
                        })
            except KeyboardInterrupt:
                # 如果用户在工具执行中 Ctrl+C，需要补齐 tools reply，
                # 否则下一次请求会因为消息历史不完整而被 API 拒绝。
                self._answer_pending_tool_calls(resp.tool_calls)
                raise

            self.context.maybe_compress(self.messages, self.llm)

        return "(reached maximum tools-call rounds)"

    def _exec_tool(self, tc) -> str:
        """执行单个工具调用，始终返回字符串结果。"""
        tool = self._tool_by_name.get(tc.name)
        if tool is None:
            return f"Error: unknown tools '{tc.name}'"

        try:
            inspect.signature(tool.execute).bind(**tc.arguments)
        except TypeError as e:
            return f"Error: bad arguments for {tc.name}: {e}"

        try:
            return tool.execute(**tc.arguments)
        except Exception as e:
            return f"Error executing {tc.name}: {e}"

    def _exec_tools_parallel(self, tool_calls, on_tool=None) -> list[str]:
        """用线程池并发执行多个工具调用。"""
        for tc in tool_calls:
            if on_tool:
                on_tool(tc.name, tc.arguments)

        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            futures = [pool.submit(self._exec_tool, tc) for tc in tool_calls]
            return [f.result() for f in futures]

    def _answer_pending_tool_calls(self, tool_calls):
        """为被中断的工具调用补一条占位回复，保持消息历史合法。"""
        answered = {m.get("tool_call_id") for m in self.messages if m.get("role") == "tools"}
        for tc in tool_calls:
            if tc.id not in answered:
                self.messages.append({
                    "role": "tools",
                    "tool_call_id": tc.id,
                    "content": "[interrupted]",
                })

    def reset(self):
        """清空会话历史。"""
        self.messages.clear()
