"""读取文件，并给每一行加上行号。"""

from pathlib import Path

from .base import Tool


class ReadFileTool(Tool):
    name = "read_file"
    description = (
        "Read a file's contents with line numbers. "
        "Always read a file before editing it."
    )
    parameters = {
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "Path to the file"},
            "offset": {"type": "integer", "description": "Start line (1-based). Default 1."},
            "limit": {"type": "integer", "description": "Max lines to read. Default 2000."},
        },
        "required": ["file_path"],
    }

    def execute(self, file_path: str, offset: int = 1, limit: int = 2000) -> str:
        try:
            # expanduser 处理 ~，resolve 转为规范的绝对路径。
            p = Path(file_path).expanduser().resolve()
            if not p.exists():
                return f"Error: {file_path} not found"
            if not p.is_file():
                return f"Error: {file_path} is a directory, not a file"

            # errors="replace" 可以避免少量坏字符导致整个读取失败。
            text = p.read_text(encoding="utf-8", errors="replace")
            lines = text.splitlines()
            total = len(lines)

            start = max(0, offset - 1)
            chunk = lines[start : start + limit]
            numbered = [f"{start + i + 1}\t{line}" for i, line in enumerate(chunk)]
            result = "\n".join(numbered)

            if total > start + limit:
                result += f"\n... ({total} lines total, showing {start + 1}-{start + len(chunk)})"
            return result or "(empty file)"
        except Exception as e:
            return f"Error: {e}"
