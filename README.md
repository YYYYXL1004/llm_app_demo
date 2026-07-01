# LLM 应用基础 Demo

这是面向小学期实践课的学生 Demo 仓库。它的目标不是覆盖所有 LLM 理论，而是让大家在服务器上跑通一条完整链路：

```text
Ollama 本地模型服务 -> OpenAI 兼容 API -> Python 后端 -> Gradio 页面
```

课堂前半段会集中讲整体思路，后面的实操时间主要按讲义自己操作。遇到问题时，优先对照 Day 4 讲义里的检查步骤排查。

## 讲义入口

- [Day 4：Ollama 部署、API 调用、RAG 与 Tool Calling](docs/day4_practical_handout.md)
- [Day 5：Agent 工作流与 AI 产品化](docs/day5_practical_handout.md)

Day 4 的目标是把服务和页面跑起来，观察 Chat、RAG、Tool Calling 三种模式。Day 5 的目标是在 Day 4 基础上理解 Workflow、Agent Fallback、状态、追问和容错。

## 文件结构

```text
llm_app_demo/
├── app.py                         # Gradio 页面入口，负责不同模式的流程分发
├── llm_client.py                  # 连接 Ollama 的 OpenAI 兼容 API
├── rag.py                         # 从 data/kb.md 做轻量检索
├── tools.py                       # Tool Calling 的 schema 和真实工具函数
├── data/kb.md                     # RAG 演示知识库
├── scripts/check_ollama.py        # 检查模型 API 连通性
├── docs/
│   ├── day4_practical_handout.md  # Day 4 实操讲义
│   └── day5_practical_handout.md  # Day 5 实操讲义
├── requirements.txt
└── .env.example
```

重点看 4 个 Python 文件：

| 文件 | 作用 |
| --- | --- |
| `app.py` | Gradio 页面和 Chat / RAG / Tool Calling / Agent Fallback 分发 |
| `llm_client.py` | 把 Ollama 当成 OpenAI 兼容 API 调用 |
| `rag.py` | 演示 RAG 的检索和上下文拼接 |
| `tools.py` | 演示如何把已有 Python 函数接入 Tool Calling |

## Day 4 最短实操路径

完整步骤见 [Day 4 实操讲义](docs/day4_practical_handout.md)。如果你只想快速确认流程，按下面顺序做。

### 1. 准备 Ollama 和模型

课程服务器已经放好了离线文件，优先从共享目录复制，不需要自己下载。

| 服务器 IP | 共享目录 |
| --- | --- |
| `183.175.12.68` | `/data/share/ollama_models` |
| `202.207.12.215` | `/data/share/ollama_models` |
| `183.175.12.113` | `/home/share/ollama_models` |

在服务器上准备目录：

```bash
mkdir -p ~/apps ~/apps/ollama ~/apps/ollama/models
```

如果你在 `183.175.12.68` 或 `202.207.12.215` 上：

```bash
cp /data/share/ollama_models/ollama-linux-amd64.tar.zst ~/apps/
cp /data/share/ollama_models/Qwen3-1.7B-Q4_K_M.gguf ~/apps/ollama/models/
```

如果你在 `183.175.12.113` 上：

```bash
cp /home/share/ollama_models/ollama-linux-amd64.tar.zst ~/apps/
cp /home/share/ollama_models/Qwen3-1.7B-Q4_K_M.gguf ~/apps/ollama/models/
```

后续解压、写 `Modelfile`、`ollama create` 的完整命令在 Day 4 讲义第 3 到第 5 节。

### 2. 启动 Ollama 服务

终端 1：

```bash
export OLLAMA_HOST=127.0.0.1:11434
ollama serve
```

这个终端不要关闭。

### 3. 配置并检查项目

终端 2：

```bash
cd llm_app_demo
conda activate 你的环境名
pip install -r requirements.txt
cp .env.example .env
```

`.env` 默认可以写成：

```text
OPENAI_BASE_URL=http://127.0.0.1:11434/v1
OPENAI_API_KEY=ollama
MODEL=Qwen3-1.7B-Q4_K_M
```

检查 API：

```bash
python scripts/check_ollama.py
```

如果能看到模型列表和 `Chat test` 回答，就说明 API 可用。模型列表里显示 `Qwen3-1.7B-Q4_K_M:latest` 是正常的，脚本会把它识别成 `Qwen3-1.7B-Q4_K_M`。

### 4. 启动页面

```bash
python app.py
```

默认访问：

```text
http://127.0.0.1:7860
```

如果你在远程服务器上运行，需要结合服务器开放端口、SSH 转发或修改 `GRADIO_SERVER_NAME`，按老师现场说明处理。

## 页面演示顺序

1. `Chat`：问“Prompt 为什么要写角色、任务和约束？”，观察普通聊天。
2. `RAG`：问“如何把任意已有 Python 函数接入 Tool Calling？”，观察检索来源。
3. `Tool Calling`：问“帮我计算 23*17+9，并告诉我 Asia/Shanghai 当前时间。”，观察工具调用记录。
4. `Agent Fallback`：问“这个怎么弄？”，观察追问和 fallback。

## Day 4 提交内容

Day 4 只提交 3 样东西，不需要写实验记录：

1. `python scripts/check_ollama.py` 成功运行的终端截图。
2. Gradio 页面成功打开的浏览器截图，截图里能看到 Chat、RAG 或 Tool Calling 任意一次回答。
3. 项目里的 `.env` 文件内容截图或文本，注意不要提交真实密码；本课程里 `OPENAI_API_KEY=ollama` 可以保留。

## 常见提示

- `Qwen3-1.7B-Q4_K_M:latest` 是 Ollama 给模型加的 tag，不是错误。
- `python app.py` 出现 `StarletteDeprecationWarning` 通常是 Gradio 依赖里的弃用提示，不影响课堂 Demo 使用。
- Tool Calling 偶尔不触发，不一定是代码坏了，小模型的工具调用能力可能不稳定，可以换更明确的问题再试。
- 如果端口 `11434` 被占用，可以换 `11435`，但 `.env` 里的 `OPENAI_BASE_URL` 也要同步修改。
- 如果 Gradio 端口 `7860` 被占用，可以在 `.env` 里设置 `GRADIO_SERVER_PORT=7861`。

## 不要上传这些文件

仓库只需要上传代码、讲义、知识库和配置模板。不要上传：

- `.env`
- `__pycache__/`
- Ollama 模型文件和安装包
- conda 环境目录
- 训练权重或大模型文件