# SimpleCoder

SimpleCoder 是一个带中文注释的轻量 Coding Agent，参照 `CoreCoder` 的核心结构整理而来。

本项目保留：

- Agent 主循环
- OpenAI-compatible LLM 调用层
- 上下文压缩
- 会话保存与恢复
- CLI 交互入口
- `simplecoder/tools/` 下的基础工具：命令执行、读文件、写文件、编辑文件、glob、grep、时间、子 Agent


## 运行

```bash
pip install -e .
simplecoder
```

或一次性执行：

```bash
simplecoder -p "帮我阅读这个项目结构"
```

## 环境变量

```bash
export OPENAI_API_KEY=sk-...
export SIMPLECODER_MODEL=gpt-5.5
```

如果使用 OpenAI-compatible 第三方接口：

```bash
export OPENAI_API_KEY=sk-...
export OPENAI_BASE_URL=https://api.deepseek.com
export SIMPLECODER_MODEL=deepseek-chat
```
