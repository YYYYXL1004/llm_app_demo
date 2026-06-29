# LLM 应用基础 Demo

这个目录是一套面向小学期实践的最小 LLM 应用项目。重点是动手跑通：在服务器上用 Ollama 启动小模型，把它封装成 OpenAI 兼容 API，再接入 Gradio 页面展示 Chat、RAG、Tool Calling 和 Agent Fallback。

文档只保留两天实操讲义：

- [Day 4：Ollama 部署、API 调用、RAG 与 Tool Calling](docs/day4_practical_handout.md)
- [Day 5：Agent 工作流与 AI 产品化](docs/day5_practical_handout.md)

Day 1 的讲义保留为写作风格参考：

- [Day 1 实操讲义](docs/day1_practical_handout.md)

## 文件结构

```text
llm_app_demo/
├── app.py                         # 页面入口，负责 Chat / RAG / Tool Calling / Agent Fallback 分发
├── llm_client.py                  # 连接 Ollama 的 OpenAI 兼容 API
├── rag.py                         # 从 data/kb.md 做轻量检索
├── tools.py                       # 定义并执行工具调用
├── data/kb.md                     # RAG 演示知识库
├── scripts/check_ollama.py        # 检查模型 API 连通性
├── docs/
│   ├── day4_practical_handout.md  # Day 4 实操讲义
│   ├── day5_practical_handout.md  # Day 5 实操讲义
│   └── day1_practical_handout.md  # Day 1 风格参考
├── requirements.txt
└── .env.example
```

重点看 4 个 Python 文件：

| 文件 | 作用 |
| --- | --- |
| `app.py` | Gradio 页面和四种模式的流程分发 |
| `llm_client.py` | 如何把 Ollama 当成 OpenAI 兼容 API 调用 |
| `rag.py` | RAG 的检索、拼接上下文 |
| `tools.py` | Tool Calling 的 schema、参数和真实函数执行 |

## 一句话架构

服务器上用 Ollama 部署小模型，暴露 OpenAI 兼容 API；Python 项目使用 `openai` SDK 连接该 API；Gradio 页面提供 Chat、RAG、Tool Calling、Agent Fallback 四种演示模式。

```text
Browser
  -> Gradio app
  -> openai SDK
  -> http://服务器IP:11434/v1/chat/completions
  -> Ollama local model
```

## 服务器部署 Ollama

文档默认面向非 sudo 用户，不要求 `systemctl` 或系统级安装。完整流程见 [Day 4 实操讲义](docs/day4_practical_handout.md)。

如果服务器已经有 Ollama，普通用户可以直接启动用户态服务：

```bash
export OLLAMA_HOST=127.0.0.1:11434
ollama serve
```

再开一个终端拉取并检查模型：

```bash
ollama create Qwen3-1.7B-Q4_K_M -f ~/apps/ollama/models/Modelfile
ollama list
curl http://127.0.0.1:11434/v1/models
```

如果没有 sudo 权限且服务器也没有 Ollama，请确认课程是否提供可执行文件或离线安装包。

## 快速开始

先确认 Ollama 服务已经启动，并且能访问：

```bash
curl http://127.0.0.1:11434/v1/models
```

再启动本项目：

```bash
cd llm_app_demo
conda activate 你的环境名
pip install -r requirements.txt
cp .env.example .env
```

按你的服务器地址修改 `.env`：

```bash
OPENAI_BASE_URL=http://127.0.0.1:11434/v1
OPENAI_API_KEY=ollama
MODEL=Qwen3-1.7B-Q4_K_M
```

检查 API：

```bash
python scripts/check_ollama.py
```

启动页面：

```bash
python app.py
```

默认访问：

```text
http://127.0.0.1:7860
```

如果模型端口、模型名称或 Gradio 端口不同，修改 `.env` 即可。

## 建议演示顺序

1. 先用 `Chat` 模式演示普通对话和 Prompt 影响。
2. 切到 `RAG` 模式，问“如何把 Day 3 工具接入 LLM？”，展示检索上下文如何进入 Prompt。
3. 切到 `Tool Calling` 模式，问“帮我计算 23*17+9，并告诉我现在时间”，展示模型选择工具、程序执行工具、模型整合结果。
4. 切到 `Agent Fallback` 模式，故意问模糊问题，展示追问、兜底、失败说明。

详细演示步骤见 [Day 4 实操讲义](docs/day4_practical_handout.md) 和 [Day 5 实操讲义](docs/day5_practical_handout.md)。

## 关键提醒

- Ollama 的 OpenAI 兼容层不是完整 OpenAI 平台，只适合复用常见 SDK 和接口格式。
- Tool Calling 是否稳定，取决于模型本身的工具调用能力。实践时要准备 fallback，避免模型不调用工具时流程卡住。
- RAG 的核心不是“把文档塞给模型”，而是“检索、压缩、引用、约束答案边界”。
- Agent 产品化的难点通常不在“会调用工具”，而在状态、错误处理、权限、审计、超时和用户体验。

## 上传前检查

仓库只需要上传代码、讲义、知识库和配置模板。不要上传：

- `.env`
- `__pycache__/`
- Ollama 模型文件
- conda 环境目录
- 训练权重或大模型文件
