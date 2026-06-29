# Day 4 实操讲义：Ollama 部署、API 调用、RAG 与 Tool Calling

> 本讲义只关注实操：在没有 sudo 权限的服务器账号下启动一个小模型服务，并把它封装成 OpenAI 兼容 API 给 Python 项目调用。  
> 今日目标不是讲清所有 LLM 原理，而是让你跑通一次“模型服务 -> API -> Gradio Demo”的完整链路。

---

## 0. 今日完成目标

完成 Day 4 后，你应该能做到：

- 判断服务器上是否已经有可用的 Ollama
- 在非 sudo 用户目录下准备 Ollama
- 启动用户态 `ollama serve`
- 拉取并测试一个小模型
- 用 OpenAI 兼容 API 调用本地模型
- 配置本项目的 `.env`
- 跑通 Chat、RAG、Tool Calling 三种模式
- 知道常见失败现象应该先查哪里

---

## 1. 非 sudo 用户先看这里

课程服务器通常不会给普通用户 sudo 权限，所以本讲义默认：

- 不使用 `sudo systemctl`
- 不修改系统服务
- 不安装 GPU 驱动
- 不写入 `/usr/local/bin`、`/usr` 等系统目录
- 所有程序、模型和项目文件都放在自己的用户目录或课程目录下

非 sudo 用户能做的事情：

| 任务 | 是否可做 | 说明 |
| --- | --- | --- |
| 运行 Python 项目 | 可以 | 使用自己的 conda 环境 |
| 启动 `ollama serve` | 可以 | 用当前账号启动前台进程 |
| 监听 `127.0.0.1:11434` | 可以 | 只给本机访问 |
| 监听 `0.0.0.0:11434` | 通常可以 | 但防火墙和安全组可能需要管理员 |
| 安装系统服务 | 不可以 | 需要 sudo |
| 安装或升级显卡驱动 | 不可以 | 需要管理员 |

如果课程服务器已经统一部署好了 Ollama，你只需要确认 API 地址，不需要自己安装。

---

## 2. 项目文件结构

```bash
cd llm_app_demo
```

本 demo 文件很少，主要看下面几类：

```text
llm_app_demo/
├── app.py                         # 页面入口和流程分发
├── llm_client.py                  # 模型 API 客户端
├── rag.py                         # RAG 检索
├── tools.py                       # Tool Calling 工具
├── data/kb.md                     # RAG 知识库
├── scripts/check_ollama.py        # API 检查脚本
├── docs/                          # 实操讲义
├── requirements.txt
└── .env.example
```

| 文件 | 用途 |
| --- | --- |
| `app.py` | 页面入口，负责四种模式的流程分发 |
| `llm_client.py` | 连接 Ollama 的 OpenAI 兼容 API |
| `rag.py` | 从 `data/kb.md` 检索资料 |
| `tools.py` | 定义工具 schema，并真正执行工具函数 |
| `data/kb.md` | RAG 演示知识库 |
| `scripts/check_ollama.py` | 检查模型 API 连通性 |
| `.env.example` | 环境变量模板，复制成 `.env` 后修改 |

整体调用关系：

```text
浏览器
-> app.py
-> llm_client.py
-> Ollama API

RAG 模式额外读取 rag.py 和 data/kb.md
Tool Calling 模式额外调用 tools.py
```

---

## 3. 检查服务器是否已有 Ollama

先直接检查：

```bash
ollama --version
```

如果能看到版本号，说明命令可用。

再检查 API 服务是否已经启动：

```bash
curl http://127.0.0.1:11434/api/tags
```

可能出现三种情况：

| 现象 | 说明 | 下一步 |
| --- | --- | --- |
| 返回 JSON | Ollama 服务已经启动 | 直接进入第 5 节 |
| `Connection refused` | 命令可能有，但服务没启动 | 执行第 4 节 |
| `ollama: command not found` | 当前账号找不到 Ollama | 执行第 3.1 节 |

### 3.1 非 sudo 准备 Ollama

如果服务器不能联网，先检查课程是否提供了可读的 Ollama Linux 离线压缩包。  
如果服务器可以联网，可以把官方二进制包下载到自己的目录：

```bash
mkdir -p ~/apps/ollama
cd ~/apps
curl -L https://ollama.com/download/ollama-linux-amd64.tgz -o ollama-linux-amd64.tgz
tar -xzf ollama-linux-amd64.tgz -C ~/apps/ollama
```

把命令加入当前终端的 `PATH`：

```bash
export PATH="$HOME/apps/ollama/bin:$PATH"
ollama --version
```

如果这一步失败，优先确认下面几件事；自己无法确认时再联系课程支持人员或服务器管理员：

- 服务器是否能访问外网
- 课程是否已经提供离线安装包
- 当前机器架构是否为 Linux x86_64
- 当前账号是否有模型目录的读写权限

---

## 4. 用户态启动 Ollama 服务

普通用户不需要 `systemctl`，直接启动前台进程：

```bash
export OLLAMA_HOST=127.0.0.1:11434
ollama serve
```

这个终端会被服务占用，不要关闭。

再开一个新的终端，测试服务：

```bash
curl http://127.0.0.1:11434/api/tags
```

如果同一台服务器上有多人同时使用，`11434` 端口可能被别人占用。可以换端口：

```bash
export OLLAMA_HOST=127.0.0.1:11435
ollama serve
```

后续项目里的 API 地址也要改成：

```text
http://127.0.0.1:11435/v1
```

### 4.1 模型文件放在哪里

Ollama 默认把模型放在：

```text
~/.ollama/models
```

如果用户目录空间不够，可以把模型目录放到自己有写权限的数据盘。先用自己的目录演示：

```bash
mkdir -p "$HOME/ollama_models"
export OLLAMA_MODELS="$HOME/ollama_models"
export OLLAMA_HOST=127.0.0.1:11434
ollama serve
```

如果课程提供了共享数据盘，例如 `/sda/data/你的用户名/ollama_models`，也可以把 `OLLAMA_MODELS` 改成那个路径。注意：`OLLAMA_MODELS` 要在 `ollama serve` 启动前设置。

---

## 5. 拉取并测试小模型

实践时优先选择稳定、能跑得动的模型，不要追求最大参数量。

```bash
ollama pull qwen3:8b
ollama list
```

如果显存或内存紧张，可以换课程指定的更小模型，例如 1.5B、3B 模型。

测试交互：

```bash
ollama run qwen3:8b
```

输入：

```text
用一句话介绍 RAG。
```

能正常回答，说明模型本身可用。输入 `/bye` 退出。

---

## 6. 测试 OpenAI 兼容 API

Ollama 的 OpenAI 兼容 API 地址格式是：

```text
http://127.0.0.1:11434/v1
```

先看模型列表：

```bash
curl http://127.0.0.1:11434/v1/models
```

再测试聊天接口：

```bash
curl http://127.0.0.1:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen3:8b",
    "messages": [
      {"role": "user", "content": "用一句话回答：OpenAI 兼容 API 是否可用？"}
    ],
    "temperature": 0
  }'
```

只要返回里有 `choices` 和 `message.content`，说明 Python 项目可以用 OpenAI SDK 调它。

---

## 7. 配置 Python 项目

回到项目目录：

```bash
cd llm_app_demo
```

激活你本地已经准备好的 conda 环境：

```bash
conda activate 你的环境名
```

安装依赖：

```bash
pip install -r requirements.txt
```

复制环境变量：

```bash
cp .env.example .env
```

编辑 `.env`：

```text
OPENAI_BASE_URL=http://127.0.0.1:11434/v1
OPENAI_API_KEY=ollama
MODEL=qwen3:8b
GRADIO_SERVER_NAME=127.0.0.1
GRADIO_SERVER_PORT=7860
```

如果你的 Ollama 用的是 `11435`，这里也要改成：

```text
OPENAI_BASE_URL=http://127.0.0.1:11435/v1
```

---

## 8. 检查项目能否调用模型

```bash
python scripts/check_ollama.py
```

正常情况下会看到：

```text
Checking Ollama OpenAI-compatible API: http://127.0.0.1:11434/v1
Model: qwen3:8b
Available models:
- qwen3:8b

Chat test:
Ollama API 可用。
```

如果提示模型不存在：

```bash
ollama list
ollama pull qwen3:8b
```

如果提示连接失败：

```bash
curl http://127.0.0.1:11434/api/tags
```

先确认 `ollama serve` 那个终端还在运行。

---

## 9. 启动 Gradio Demo

```bash
python app.py
```

默认访问：

```text
http://127.0.0.1:7860
```

如果你在远程服务器上运行项目，浏览器在自己电脑上，可以用 SSH tunnel：

```bash
ssh -L 7860:127.0.0.1:7860 用户名@服务器IP
```

然后在自己电脑浏览器打开：

```text
http://127.0.0.1:7860
```

如果需要让其他人从局域网访问你的 Gradio 页面，把 `.env` 改成：

```text
GRADIO_SERVER_NAME=0.0.0.0
GRADIO_SERVER_PORT=7860
```

然后访问：

```text
http://服务器IP:7860
```

如果访问不了，通常不是 Python 代码问题，而是服务器防火墙、安全组或校园网策略需要管理员放行。

---

## 10. 页面演示 1：普通 Chat 与 Prompt

页面模式选择：

```text
Chat
```

输入：

```text
Prompt 为什么要写角色、任务和约束？
```

观察模型回答。

然后修改页面里的 `System Prompt`：

```text
你是严谨的课程助教。回答必须分三点，每点不超过 30 字。不确定就说不知道。
```

再次输入同一个问题。

这一步强调：

- Prompt 可以改变语气、结构和输出格式
- Prompt 可以设置“不知道就说不知道”
- Prompt 不能让模型自动知道私有资料或实时信息

---

## 11. 页面演示 2：RAG

页面模式选择：

```text
RAG
```

输入：

```text
如何把 Day 3 工具接入 LLM？
```

观察页面回答底部的：

```text
检索到的资料：
```

本项目的 RAG 流程：

```text
用户问题
-> rag.py 从 data/kb.md 检索相关片段
-> app.py 把片段拼进 Prompt
-> llm_client.py 调用模型
-> 页面返回答案和检索来源
```

RAG 要解决的是“模型缺少私有知识或课程资料”的问题。

它不是重新训练模型，也不能保证文档质量。资料写错了，模型也会跟着错。

---

## 12. 页面演示 3：Tool Calling

页面模式选择：

```text
Tool Calling
```

输入：

```text
帮我计算 23*17+9，并告诉我 Asia/Shanghai 当前时间。
```

正常情况下，回答底部会出现：

```text
工具调用记录：
```

本项目提供了三个工具：

| 工具 | 作用 |
| --- | --- |
| `calculator` | 安全四则运算 |
| `get_current_time` | 查询指定时区当前时间 |
| `day3_tool_status` | 模拟调用 Day 3 工具状态 |

Tool Calling 的关键点：

```text
模型只负责决定是否调用工具和填参数
Python 后端才真正执行工具
```

如果模型没有调用工具，页面会提示：

```text
本次模型没有发起 tool call
```

这不是项目坏了，而是小模型的 tool calling 能力可能不稳定。工程上要准备 fallback。

---

## 13. 如何把 Day 3 工具接入 LLM

假设 Day 3 已经写好了一个普通 Python 函数：

```python
def search_api(query: str) -> list[dict]:
    ...
```

接入步骤：

1. 保持它是一个清晰的普通函数。
2. 在 `tools.py` 里写一个 JSON Schema，告诉模型工具名、参数和用途。
3. 把 schema 加入 `TOOL_SCHEMAS`。
4. 在 `run_tool()` 里根据工具名调用真实函数。
5. 在 `app.py` 里把 `TOOL_SCHEMAS` 传给模型。
6. 模型返回 tool call 后，由 Python 执行工具。
7. 工具结果作为 `tool` message 回填给模型。

关键原则：

```text
模型不能直接访问你的系统，只能通过你暴露的函数边界访问。
```

---

## 14. LLM 常见失败案例

| 失败现象 | 常见原因 | 工程处理 |
| --- | --- | --- |
| 编造命令或事实 | 模型缺资料 | 用 RAG、引用来源 |
| 没按 JSON 输出 | 格式约束不够或模型能力不足 | 结构化输出、校验、重试 |
| 没调用工具 | 小模型 tool calling 不稳定 | 改 Prompt、换模型、写 fallback |
| 工具参数错 | schema 不清楚或用户信息缺失 | 参数校验、追问 |
| 回答太慢 | 模型太大或上下文太长 | 换小模型、减少 top_k |
| 连接失败 | 服务没启动或端口不对 | 查 `ollama serve` 和 `.env` |

---

## 15. 今日检查清单

结束前确认：

- `ollama serve` 正在运行
- `ollama list` 能看到模型
- `curl http://127.0.0.1:11434/v1/models` 有返回
- `.env` 的 `OPENAI_BASE_URL` 和端口正确
- `python scripts/check_ollama.py` 能返回聊天测试
- `python app.py` 能打开 Gradio 页面
- Chat、RAG、Tool Calling 至少各跑通一次
