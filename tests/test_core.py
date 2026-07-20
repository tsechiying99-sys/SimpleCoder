"""Core module smoke tests for SimpleCoder."""

from simplecoder import ALL_TOOLS, Agent, Config, LLM, __version__
from simplecoder.context import ContextManager, estimate_tokens
from simplecoder.prompt import system_prompt
from simplecoder.tools import get_tool


def test_version():
    assert __version__ == "0.1.0"


def test_public_api_exports():
    assert Agent is not None
    assert LLM is not None
    assert Config is not None
    assert len(ALL_TOOLS) == 8


def test_config_from_env_prefers_simplecoder_vars(monkeypatch):
    monkeypatch.setenv("SIMPLECODER_MODEL", "simple-model")
    monkeypatch.setenv("MODEL_NAME", "fallback-model")
    monkeypatch.setenv("SIMPLECODER_API_KEY", "test-key")

    config = Config.from_env()

    assert config.model == "simple-model"
    assert config.api_key == "test-key"


def test_config_defaults(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    # 测试默认值时，不加载项目根目录里的 .env，
    # 否则 .env 里的 MODEL_NAME 会覆盖默认模型。
    monkeypatch.setattr("simplecoder.config._load_dotenv", lambda: None)

    monkeypatch.delenv("SIMPLECODER_MODEL", raising=False)
    monkeypatch.delenv("MODEL_NAME", raising=False)
    monkeypatch.delenv("SIMPLECODER_MAX_TOKENS", raising=False)
    monkeypatch.delenv("SIMPLECODER_TEMPERATURE", raising=False)

    config = Config.from_env()

    assert config.model == "gpt-5.5"
    assert config.max_tokens == 4096
    assert config.temperature == 0.0


def test_system_prompt_lists_available_tools():
    prompt = system_prompt([get_tool("read_file"), get_tool("write_file")])

    assert "SimpleCoder" in prompt
    assert "read_file" in prompt
    assert "write_file" in prompt


def test_estimate_tokens_counts_message_content():
    tokens = estimate_tokens([{"role": "user", "content": "hello world"}])

    assert tokens > 0
    assert tokens < 100


def test_context_snips_verbose_tool_output():
    ctx = ContextManager(max_tokens=3000)
    messages = [{"role": "tool", "tool_call_id": "t1", "content": "line\n" * 1000}]

    before = estimate_tokens(messages)
    changed = ctx._snip_tool_outputs(messages)
    after = estimate_tokens(messages)

    assert changed is True
    assert after < before


def test_context_safe_split_never_starts_tail_with_tool_reply():
    ctx = ContextManager(max_tokens=1000)
    messages = [
        {"role": "user", "content": "run tool"},
        {"role": "assistant", "content": None, "tool_calls": [{"id": "call-1"}]},
        {"role": "tool", "tool_call_id": "call-1", "content": "result"},
    ]

    split = ctx._safe_split(messages, keep_recent=1)

    assert messages[split].get("role") != "tool"
