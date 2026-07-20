"""配置读取：环境变量 + 默认值。

SimpleCoder 默认使用 OpenAI-compatible API，因此 DeepSeek、Qwen、Kimi、
Ollama 等只要提供兼容接口，通常都可以通过 base_url 接入。
"""

import os
from dataclasses import dataclass
from pathlib import Path


def _load_dotenv():
    """从当前目录向上查找 .env；未安装 python-dotenv 时静默跳过。"""
    try:
        from dotenv import load_dotenv

        env_path = Path(".env")
        if not env_path.exists():
            cur = Path.cwd()
            home = Path.home()
            while cur != home and cur != cur.parent:
                candidate = cur / ".env"
                if candidate.exists():
                    env_path = candidate
                    break
                cur = cur.parent
        load_dotenv(env_path, override=False)
    except ImportError:
        pass

@dataclass
class Config:
    model: str = "gpt-5.5"
    api_key: str = ""
    base_url: str | None = None
    max_tokens: int = 4096
    temperature: float = 0.0
    max_context_tokens: int = 128_000
    provider: str = "openai"

    @classmethod
    def from_env(cls) -> "Config":
        """从环境变量构造配置，SimpleCoder 变量优先。"""
        _load_dotenv()
        api_key = (
            os.getenv("SIMPLECODER_API_KEY")
            or os.getenv("OPENAI_API_KEY")
            or os.getenv("DEEPSEEK_API_KEY")
            or ""
        )
        return cls(
            model=os.getenv("SIMPLECODER_MODEL") or os.getenv("MODEL_NAME", "gpt-5.5"),
            api_key=api_key,
            base_url=os.getenv("OPENAI_BASE_URL") or os.getenv("SIMPLECODER_BASE_URL"),
            max_tokens=int(os.getenv("SIMPLECODER_MAX_TOKENS", "4096")),
            temperature=float(os.getenv("SIMPLECODER_TEMPERATURE", "0")),
            max_context_tokens=int(os.getenv("SIMPLECODER_MAX_CONTEXT", "128000")),
            provider=os.getenv("SIMPLECODER_PROVIDER", "openai"),
        )
