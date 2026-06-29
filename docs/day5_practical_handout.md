# Day 5 实操讲义：Agent 工作流与 AI 产品化

> 本讲义只关注实操：把 Day 4 已经跑通的模型 API 包装成更像产品的交互流程。  
> 今日目标不是做一个完全自主 Agent，而是让你理解 Chatbot、Workflow、Agent 的区别，并在 Gradio 页面里观察状态、追问、重试和 fallback。

---

## 0. 今日完成目标

完成 Day 5 后，你应该能做到：

- 说清 Chatbot、Workflow、Agent 的工程区别
- 判断什么时候该用 RAG，什么时候该用 Tool Calling
- 理解为什么产品里要显式管理状态
- 设计缺参数时的追问
- 给模型调用和工具调用加重试与 fallback
- 看懂本项目的 Gradio 页面结构
- 把 Day 4 的 Demo 讲成一个小型 AI 产品原型

---

## 1. 开始前检查

先确认 Day 4 的服务还可用。

终端 1：启动 Ollama。

```bash
export OLLAMA_HOST=127.0.0.1:11434
ollama serve
```

这个终端要一直开着，后面的检查和页面演示都依赖它。

终端 2：进入项目并激活环境。

```bash
cd llm_app_demo
conda activate 你的环境名
python scripts/check_ollama.py
```

能看到聊天测试输出后，启动页面：

```bash
python app.py
```

浏览器打开：

```text
http://127.0.0.1:7860
```

如果 Day 4 使用的是其他端口，先检查 `.env`：

```text
OPENAI_BASE_URL=http://127.0.0.1:11434/v1
MODEL=Qwen3-1.7B-Q4_K_M
```

---

## 2. 三种形态：Chatbot、Workflow、Agent

### 2.1 Chatbot

```text
用户输入 -> 模型 -> 回复
```

适合：

- 问答
- 内容生成
- 解释概念
- 修改文本

缺点：

- 没有外部资料时容易编造
- 不能可靠执行动作
- 很难保证流程稳定

本项目里的对应模式：

```text
Chat
```

### 2.2 Workflow

```text
用户输入
-> 固定步骤 1：校验输入
-> 固定步骤 2：检索资料或调用工具
-> 固定步骤 3：模型总结
-> 返回结果
```

适合：

- 课程问答
- 报告生成
- 客服分流
- 表单处理
- 有明确步骤的业务流程

优点：

- 可控
- 好调试
- 容易加日志和权限
- 更适合课程项目和真实产品第一版

本项目里的对应模式：

```text
RAG
Tool Calling
```

### 2.3 Agent

```text
用户输入
-> 模型判断下一步
-> 追问 / 检索 / 调工具 / 重试 / 结束
-> 返回结果
```

适合：

- 目标开放
- 步骤不固定
- 需要模型参与决策
- 允许多轮试错

风险：

- 更难调试
- 更容易循环调用工具
- 更需要状态、权限、超时和 fallback
- 小模型上稳定性通常不如固定 Workflow

本项目里的对应模式：

```text
Agent Fallback
```

实践建议：

```text
先做 Workflow，再在关键节点加入 Agent 决策。
```

---

## 3. 本项目文件结构

```text
llm_app_demo/
├── app.py                         # 页面入口和流程分发
├── llm_client.py                  # 模型 API 客户端
├── rag.py                         # RAG 检索
├── tools.py                       # Tool Calling 工具
├── data/kb.md                     # RAG 知识库
├── scripts/check_ollama.py        # API 检查脚本
├── docs/                          # 两天讲义
├── requirements.txt
└── .env.example
```

理解项目时先抓住这条链路：

```text
浏览器 -> app.py -> llm_client.py -> Ollama
```

两种增强流程：

```text
RAG: app.py -> rag.py -> data/kb.md -> llm_client.py
Tool Calling: app.py -> tools.py -> llm_client.py
```

核心文件说明：

| 文件 | 作用 |
| --- | --- |
| `app.py` | 页面、模式选择、主流程 |
| `llm_client.py` | 封装模型 API 调用 |
| `rag.py` | 从 `data/kb.md` 检索资料 |
| `tools.py` | 定义工具 schema 和真实执行函数 |
| `scripts/check_ollama.py` | 检查服务是否可用 |

---

## 4. 工具选择：什么时候用什么

遇到一个用户问题，先问三个问题。

| 判断问题 | 如果答案是“是” | 推荐做法 |
| --- | --- | --- |
| 需要课程资料、私有文档或最新文档吗？ | 是 | RAG |
| 需要精确计算、当前时间、数据库或业务 API 吗？ | 是 | Tool Calling |
| 用户目标不清楚、参数不完整吗？ | 是 | 追问 |
| 步骤固定且可预期吗？ | 是 | Workflow |
| 步骤不固定，需要模型决定下一步吗？ | 是 | Agent |

不要让模型凭空回答这些问题：

- 当前时间
- 实时价格
- 数据库查询结果
- 文件内容
- 账户状态
- 课程资料里没有写的具体要求

---

## 5. 状态管理

很多初学者会误以为“聊天历史就是状态”。真实产品里不够。

一个可靠流程至少要显式记录：

| 状态字段 | 例子 |
| --- | --- |
| 用户原始目标 | “帮我把 Day 3 search_api 接入 LLM” |
| 已知参数 | `tool_name=search_api` |
| 缺失参数 | 还不知道输入输出格式 |
| 当前阶段 | `need_more_info`、`retrieving`、`calling_tool` |
| 历史消息 | 最近几轮对话 |
| 工具调用记录 | 调用了什么、参数是什么、结果是什么 |
| 错误次数 | 当前工具失败了几次 |
| fallback 原因 | 模型没调工具、检索为空、参数不合法 |

本项目为了教学保持简单，主要通过 `history`、`mode`、`top_k`、`system_prompt` 表示状态。  
真实产品建议单独维护一个 `state` 对象，不要只依赖模型记忆。

---

## 6. 追问：不要乱猜用户意图

页面模式选择：

```text
Agent Fallback
```

输入：

```text
这个怎么弄？
```

预期行为：

```text
这个问题的信息不足。请补充目标、输入、期望输出和当前报错。
```

这一步要强调：

- 用户问题模糊时，可靠系统应该追问
- 不要为了显得智能而猜测用户想做什么
- 追问要具体告诉用户补什么

更好的追问格式：

```text
你想完成哪个任务？请补充：
1. 目标是什么
2. 输入数据是什么
3. 希望输出什么
4. 当前报错或卡住的位置
```

---

## 7. 重试：只重试临时错误

适合重试：

- 网络超时
- 模型偶发返回空内容
- 模型输出 JSON 少了括号
- 工具服务临时不可用

不适合重试：

- 用户没提供关键参数
- 权限不足
- 工具不存在
- 数据本身不存在
- Prompt 写错导致每次都错

推荐规则：

```text
最多重试 1 到 2 次。
每次重试都要记录原因。
重试后仍失败，进入 fallback。
```

可以用这个流程理解：

```text
调用模型失败
-> 再试一次
-> 仍失败
-> 告诉用户哪一步失败
-> 提供下一步操作
```

---

## 8. Fallback：失败后要能继续用

不好的 fallback：

```text
出错了。
```

好的 fallback：

```text
自动流程失败，已进入 fallback。

失败原因：模型服务连接失败。

可执行的下一步：
1. 检查 ollama serve 是否还在运行
2. 检查 .env 里的 OPENAI_BASE_URL
3. 运行 python scripts/check_ollama.py
```

本项目在 `app.py` 里有两类 fallback：

| 位置 | 行为 |
| --- | --- |
| `run_tool_calling()` | 模型没发起 tool call 时，提示换模型或换问题 |
| `respond()` | API 调用异常时，提示当前 base_url 和 model |

产品化时，fallback 不是临时补丁，而是用户体验的一部分。

---

## 9. 页面演示流程

### 9.1 Chatbot

模式：

```text
Chat
```

输入：

```text
Prompt 为什么要写角色、任务和约束？
```

讲解：

- 这就是最简单的 Chatbot
- 只有聊天历史和 System Prompt
- 没有检索，也没有工具

### 9.2 Workflow：RAG

模式：

```text
RAG
```

输入：

```text
如何把 Day 3 工具接入 LLM？
```

讲解：

- 先检索 `data/kb.md`
- 再把资料拼进 Prompt
- 最后让模型基于资料回答
- 页面底部显示检索来源

### 9.3 Workflow：Tool Calling

模式：

```text
Tool Calling
```

输入：

```text
帮我计算 23*17+9，并告诉我 Asia/Shanghai 当前时间。
```

讲解：

- 模型不应该假装知道当前时间
- 模型输出 tool call
- Python 后端执行 `calculator` 和 `get_current_time`
- 工具结果回填给模型
- 页面展示工具调用记录

### 9.4 Agent Fallback

模式：

```text
Agent Fallback
```

先输入：

```text
这个怎么弄？
```

讲解：

- 信息不足时先追问
- 不要让 Agent 瞎猜

再输入：

```text
如何把 Day 3 的 search_api 接入 LLM？
```

讲解：

- 当前 demo 用简单规则选择 RAG 或 Tool Calling
- 真实 Agent 会让模型参与更多决策
- 但仍然要有状态、限制和 fallback

---

## 10. Gradio 页面结构

本项目使用 `gr.Blocks` 组织页面。

页面主要部分：

| 组件 | 作用 |
| --- | --- |
| `gr.Markdown` | 显示标题、当前模型和 API |
| `gr.Dropdown` | 切换 Chat、RAG、Tool Calling、Agent Fallback |
| `gr.Slider` | 调整 `temperature` 和 `top_k` |
| `gr.Textbox` | 修改 System Prompt |
| `gr.ChatInterface` | 聊天主界面 |

数据流：

```text
用户输入
-> ChatInterface 调用 respond()
-> respond() 根据 mode 分发
-> run_chat / run_rag / run_tool_calling / run_agent_fallback
-> 返回文本给页面
```

这里重点不是 Gradio API 细节，而是看清：

- 同一个页面可以承载多种 LLM 应用形态
- 模式切换其实就是后端流程切换
- UI 控件会变成后端函数参数

---

## 11. 从 Demo 到产品要补什么

当前项目适合课程实践，但还不是完整生产系统。

如果要继续产品化，至少要补：

| 能力 | 为什么需要 |
| --- | --- |
| 用户登录 | 区分不同用户和权限 |
| 请求日志 | 排查问题和复盘工具调用 |
| 超时控制 | 防止模型或工具长时间卡住 |
| 参数校验 | 防止错误输入进入业务系统 |
| 权限确认 | 高风险操作不能自动执行 |
| 结果缓存 | 降低重复调用成本 |
| 更强检索 | 用 embedding、向量库或搜索引擎替换轻量关键词检索 |
| 评测集 | 判断 Prompt、RAG、工具调用改动是否变好 |

---

## 12. 今日检查清单

结束前确认你能讲清：

- Chatbot、Workflow、Agent 的区别
- RAG 解决的是“缺资料”
- Tool Calling 解决的是“要行动或要精确结果”
- Agent 不是越自主越好，产品里要可控
- 状态不能只靠聊天历史
- 缺参数时要追问
- 临时错误才适合重试
- fallback 要告诉用户下一步怎么做
- Gradio 页面里每个控件对应后端哪个参数
