"""创建或完整覆盖文件。"""

from pathlib import Path

from .base import Tool
from .edit import _changed_files


class WriteFileTool(Tool):
    name = "write_file"
    description = (
        "Create a new file or completely overwrite an existing one. "
        "For small edits to existing files, prefer edit_file instead."
    )
    parameters = {
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "Path for the file"},
            "content": {"type": "string", "description": "Full file content to write"},
        },
        "required": ["file_path", "content"],
    }

    def execute(self, file_path: str, content: str) -> str:
        try:
            p = Path(file_path).expanduser().resolve()
            # 自动创建父目录；目录已存在时不报错。
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")

            # 记录本轮会话改过哪些文件，供 /diff 命令展示。
            _changed_files.add(str(p))
            n_lines = content.count("\n") + (1 if content and not content.endswith("\n") else 0)
            return f"Wrote {n_lines} lines to {file_path}"
        except Exception as e:
            return f"Error: {e}"
