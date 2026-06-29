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

| 任务                   | 是否可做 | 说明                           |
| ---------------------- | -------- | ------------------------------ |
| 运行 Python 项目       | 可以     | 使用自己的 conda 环境          |
| 启动 `ollama serve`    | 可以     | 用当前账号启动前台进程         |
| 监听 `127.0.0.1:11434` | 可以     | 只给本机访问                   |
| 安装系统服务           | 不可以   | 需要 sudo                      |
| 安装或升级显卡驱动     | 不可以   | 需要管理员                     |

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

| 文件                      | 用途                                |
| ------------------------- | ----------------------------------- |
| `app.py`                  | 页面入口，负责四种模式的流程分发    |
| `llm_client.py`           | 连接 Ollama 的 OpenAI 兼容 API      |
| `rag.py`                  | 从 `data/kb.md` 检索资料            |
| `tools.py`                | 定义工具 schema，并真正执行工具函数 |
| `data/kb.md`              | RAG 演示知识库                      |
| `scripts/check_ollama.py` | 检查模型 API 连通性                 |
| `.env.example`            | 环境变量模板，复制成 `.env` 后修改  |

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

| 现象                        | 说明                     | 下一步          |
| --------------------------- | ------------------------ | --------------- |
| 返回 JSON                   | Ollama 服务已经启动      | 直接进入第 5 节 |
| `Connection refused`        | 命令可能有，但服务没启动 | 执行第 4 节     |
| `ollama: command not found` | 当前账号找不到 Ollama    | 执行第 3.1 节   |

### 3.1 非 sudo 准备 Ollama

如果服务器上已经准备好了 Ollama，你可以跳过安装部分，直接从第 4 节开始启动服务。下面这段流程适合需要自己动手完成部署的人。

如果服务器上直接下载 Ollama 比较麻烦，推荐先在你的 Windows 电脑上把安装包下载好，再传到服务器上解压。

在 Windows PowerShell 或 CMD 里执行：

```powershell
curl.exe -L https://ollama.com/download/ollama-linux-amd64.tar.zst -o ollama-linux-amd64.tar.zst
```

下载完成后，把这个文件传到服务器的某个目录，例如 `~/apps/`。先在服务器上准备目录：

```bash
mkdir -p ~/apps ~/apps/ollama
```

然后从 Windows 传过去：

```bash
scp ollama-linux-amd64.tar.zst 你的用户名@服务器IP:~/apps/
```

备注：如果文件比较大，`scp` 传几分钟是正常的。

登录服务器后，进入文件所在目录并解压：

```bash
cd ~/apps
tar --use-compress-program=unzstd -xvf ollama-linux-amd64.tar.zst -C ~/apps/ollama
```

如果你的服务器没有 `unzstd`，可以先试：

```bash
zstd -d ollama-linux-amd64.tar.zst -o ollama-linux-amd64.tar
tar -xvf ollama-linux-amd64.tar -C ~/apps/ollama
```

解压后，把命令加入当前终端的 `PATH`：

```bash
export PATH="$HOME/apps/ollama/bin:$PATH"
ollama --version
```

如果想让新开的终端也默认能找到 `ollama`，把这条路径写进 `~/.bashrc`：

```bash
echo 'export PATH="$HOME/apps/ollama/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

如果这一步失败，优先确认下面几件事；自己无法确认时再联系课程支持人员或服务器管理员：

- Windows 上下载下来的文件是否真的是 `tar.zst`
- 传到服务器时文件有没有损坏
- 当前机器架构是否为 Linux x86_64
- 当前账号是否有 `~/apps/ollama` 的读写权限

---

## 4. 用户态启动 Ollama 服务

普通用户不需要 `systemctl`，直接启动前台进程：

```bash
export OLLAMA_HOST=127.0.0.1:11434
ollama serve
```

这个终端会被服务占用，不要关闭。

后面的第 5 节到第 9 节都默认这个 `ollama serve` 还在运行。  
如果你把这个终端关掉了，后面检查 API 时就会连不上。

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

---

## 5. 导入并测试课程模型

这一节只保留一条标准路线：`Qwen3-1.7B-Q4_K_M.gguf` -> `ollama create` -> `ollama run`。

### 5.1 方式一：用 GGUF 导入

下面这套流程按 Windows 电脑 + Linux 服务器来写。

#### 第 1 步：在 Windows 上下载 GGUF 文件

先在你的 Windows 电脑上新建一个下载目录，比如：

```text
D:\ollama-models\
```

打开 PowerShell 或 CMD，切到这个目录：

```powershell
cd D:\ollama-models
```

然后下载一个 `Qwen3-1.7B-Q4_K_M.gguf` 文件。这个课程后面的示例默认就用这个文件。

```text
Qwen3-1.7B-Q4_K_M.gguf
```

如果你手上已经有课程提供的 GGUF 文件，也可以直接放到这个目录里，不必重新下载。

模型信息/原始权重入口：

- [ModelScope 的 Qwen3-1.7B-GGUF 文件页](https://modelscope.cn/models/unsloth/Qwen3-1.7B-GGUF/files)

你只需要从这个页面下载 `Qwen3-1.7B-Q4_K_M.gguf`。这份讲义后面只使用这一份模型文件，不再使用其他备选模型。

#### 第 2 步：把 GGUF 传到服务器

先在服务器上创建一个放模型的目录：

```bash
mkdir -p ~/apps/ollama/models
```

然后在 Windows 上执行 `scp`，把 GGUF 传到服务器：

```powershell
scp D:\ollama-models\Qwen3-1.7B-Q4_K_M.gguf 你的用户名@服务器IP:~/apps/ollama/models/
```

传完后，到服务器上确认文件在不在：

```bash
ls -lh ~/apps/ollama/models/
```

#### 第 3 步：在服务器上写 Modelfile

在服务器上进入模型目录：

```bash
cd ~/apps/ollama/models
```

新建一个 `Modelfile`：

```bash
nano Modelfile
```

写入下面内容：

```text
FROM ./Qwen3-1.7B-Q4_K_M.gguf
```

如果你的文件名不是这个，就把 `FROM` 后面的文件名改成你自己的实际文件名。

#### 第 4 步：用 Ollama 导入模型

在 `~/apps/ollama/models` 目录下执行：

```bash
ollama create Qwen3-1.7B-Q4_K_M -f Modelfile
```

这一步会把 GGUF 导入成一个本地 Ollama 模型。

#### 第 5 步：测试模型

导入完成后，直接测试：

```bash
ollama run Qwen3-1.7B-Q4_K_M
```

输入一句话，比如：

```text
你好，简单介绍一下你自己。
```

如果能正常回答，说明这个模型已经可以给后面的 API 和 Gradio 页面使用了。

这条路线就是本课程的标准路线。

### 5.2 方式二：直接使用课程预置模型

如果服务器上已经准备好了这个模型，你直接测试交互。

测试交互：

```bash
ollama run Qwen3-1.7B-Q4_K_M
```

输入：

```text
用一句话介绍 RAG。
```

能正常回答，说明模型本身可用。输入 `/bye` 退出。

### 5.3 模型大小和机器要求

对 2080Ti 这类 11GB 显存的机器，这份 `Qwen3-1.7B-Q4_K_M.gguf` 是比较均衡的选择。

课堂实践里可以先按这个经验值准备：

- 11GB 显存：优先选 `Qwen3-1.7B-Q4_K_M`
- 纯 CPU：能跑，但速度会慢

这门实践课后面的示例都默认使用这个模型。

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
    "model": "Qwen3-1.7B-Q4_K_M",
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

如果你在服务器上直接装包时报 `SSLEOFError`、`Could not fetch URL`，优先换成国内镜像源再装：

```bash
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
```

你也可以把镜像源写成默认配置，这样以后每次 `pip install` 都会先走镜像：

```bash
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

复制环境变量：

```bash
cp .env.example .env
```

编辑 `.env`：

```text
OPENAI_BASE_URL=http://127.0.0.1:11434/v1
OPENAI_API_KEY=ollama
MODEL=Qwen3-1.7B-Q4_K_M
GRADIO_SERVER_NAME=127.0.0.1
GRADIO_SERVER_PORT=7860
```

如果你的 Ollama 用的是 `11435`，这里也要改成：

```text
OPENAI_BASE_URL=http://127.0.0.1:11435/v1
```

---

## 8. 检查项目能否调用模型

先确认上一节启动的 `ollama serve` 还开着。

```bash
python scripts/check_ollama.py
```

正常情况下会看到：

```text
Checking Ollama OpenAI-compatible API: http://127.0.0.1:11434/v1
Model: Qwen3-1.7B-Q4_K_M
Available models:
- Qwen3-1.7B-Q4_K_M

Chat test:
Ollama API 可用。
```

如果提示模型不存在：

```bash
ollama list
ollama create Qwen3-1.7B-Q4_K_M -f ~/apps/ollama/models/Modelfile
```

如果 `ollama create` 失败，先检查 `~/apps/ollama/models/Modelfile` 和 `Qwen3-1.7B-Q4_K_M.gguf` 是否在同一个目录里。

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

| 工具               | 作用                    |
| ------------------ | ----------------------- |
| `calculator`       | 安全四则运算            |
| `get_current_time` | 查询指定时区当前时间    |
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

| 失败现象       | 常见原因                    | 工程处理                       |
| -------------- | --------------------------- | ------------------------------ |
| 编造命令或事实 | 模型缺资料                  | 用 RAG、引用来源               |
| 没按 JSON 输出 | 格式约束不够或模型能力不足  | 结构化输出、校验、重试         |
| 没调用工具     | 小模型 tool calling 不稳定  | 改 Prompt、换模型、写 fallback |
| 工具参数错     | schema 不清楚或用户信息缺失 | 参数校验、追问                 |
| 回答太慢       | 模型太大或上下文太长        | 换小模型、减少 top_k           |
| 连接失败       | 服务没启动或端口不对        | 查 `ollama serve` 和 `.env`    |

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
