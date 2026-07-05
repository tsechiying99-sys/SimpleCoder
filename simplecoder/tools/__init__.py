"""工具注册表。

Agent 会把这里的 ALL_TOOLS 转成模型可见的 function schema。
本项目刻意不包含 RAG 工具、FastAPI 服务和前端代码。
"""

from .agent import AgentTool
from .bash import BashTool
from .edit import EditFileTool
from .glob_tool import GlobTool
from .grep import GrepTool
from .now import NowTool
from .read import ReadFileTool
from .write import WriteFileTool

ALL_TOOLS = [
    BashTool(),
    ReadFileTool(),
    WriteFileTool(),
    EditFileTool(),
    GlobTool(),
    GrepTool(),
    AgentTool(),
    NowTool(),
]


def get_tool(name: str):
    """按名字查找工具。"""
    for t in ALL_TOOLS:
        if t.name == name:
            return t
    return None
