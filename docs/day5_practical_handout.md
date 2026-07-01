# Day 5 实操讲义：从 Prompt 到 Loop

> 今天不布置新的硬编码任务。  
> 目标是理清 AI Agent 工程里几个容易混在一起的概念：Prompt、Context、Harness、Workflow、Loop、Agent，并为 Day 6 项目演示做准备。

---

## 0. 今日目标

- 看懂大模型应用从 Prompt 到 Loop 的演进
- 知道 `Agent = Model + Harness` 这句话是什么意思
- 区分 Context、Tool Calling、Harness、Workflow、Loop
- 判断自己的项目属于哪种系统形态
- 准备 Day 6 的演示问题和备用方案

---

## 1. 课前检查

确认 Day 4 项目还能跑：

```bash
export OLLAMA_HOST=127.0.0.1:11434
ollama serve
```

另开终端：

```bash
cd llm_app_demo
conda activate 你的环境名
python scripts/check_ollama.py
python app.py
```

浏览器访问：

```text
http://127.0.0.1:7860
```

如果你用了其他端口，检查 `.env`：

```text
OPENAI_BASE_URL=http://127.0.0.1:11434/v1
MODEL=Qwen3-1.7B-Q4_K_M
```

---

## 2. 一条主线

今天只抓一条主线：

```text
Prompt
-> Context
-> Tool
-> Harness
-> Workflow
-> Loop
-> Agent
```

每一层都在解决一个具体问题：

| 概念 | 解决的问题 |
| --- | --- |
| Prompt | 怎么问模型 |
| Context | 给模型看什么 |
| Tool | 模型自己做不到什么 |
| Harness | 谁来组织模型、上下文、工具和运行环境 |
| Workflow | 固定步骤怎么稳定执行 |
| Loop | 系统如何观察结果后继续行动 |
| Agent | 模型如何参与下一步决策 |

不要把这些词当成互相替代的产品名。  
它们是不同层次的工程概念。

---

## 3. Prompt Engineering：怎么问模型

Prompt Engineering 关注的是输入怎么写。

典型结构：

```text
角色
+ 任务
+ 约束
+ 示例
+ 用户问题
-> 模型回答
```

例子：

```text
你是课程助教。
请用三点回答学生问题。
每点不超过 30 字。
如果资料不足，请说不知道。
```

Prompt 能控制：

- 语气
- 格式
- 角色
- 输出长度
- 是否引用资料
- 不确定时如何回答

Prompt 不能解决：

- 模型不知道实时天气
- 模型看不到本地文件
- 模型不知道服务有没有启动
- 模型不能确认代码是否通过测试
- 模型不能凭空知道课程私有资料

对应 Day 4：

```text
Chat 模式主要是 Prompt。
```

---

## 4. Context Engineering：给模型看什么

Context Engineering 关注的不是“怎么问”，而是“给模型看什么”。

典型结构：

```text
Prompt
+ 用户问题
+ 历史对话
+ 当前文件
+ 检索结果
+ 报错日志
+ 项目说明
-> 模型回答
```

Context 可以来自：

- 用户刚输入的问题
- 历史对话
- 当前代码文件
- README
- 课程资料
- RAG 检索片段
- 工具返回结果
- 终端报错

关键区别：

```text
Prompt 决定模型按什么方式回答。
Context 决定模型基于什么信息回答。
```

RAG 是一种典型的 Context Engineering：

```text
用户问题
-> 检索相关资料
-> 把资料放进上下文
-> 让模型基于资料回答
```

Context 的局限：

- 上下文太长会变慢
- 无关资料会干扰模型
- 检索错了，模型也会跟着错
- Context 只能“给信息”，不能替模型执行动作

对应 Day 4：

```text
RAG 模式 = 用 data/kb.md 给模型补上下文。
```

---

## 5. Tool：让模型获得外部能力

有些问题不是缺上下文，而是必须访问真实世界或执行动作。

例如：

- 当前时间
- 天气
- 汇率
- 股票价格
- 数据库查询
- 本地文件内容
- 服务状态
- 测试结果

这些不应该靠模型猜。

Tool Calling 的结构：

```text
用户问题
-> 模型判断需要哪个工具
-> 模型生成工具名和参数
-> Python 后端执行工具
-> 工具结果回填给模型
-> 模型生成最终回答
```

关键原则：

```text
模型负责判断和填参数。
程序负责真实执行。
```

好工具应该提供模型没有的能力。

| 好工具 | 原因 |
| --- | --- |
| `get_current_time(timezone)` | 当前时间必须实时查询 |
| `get_weather(city)` | 天气不能靠模型记忆 |
| `check_url_status(url)` | 服务状态必须实际请求 |
| `read_project_file(path)` | 模型默认看不到本地文件 |
| `run_tests(command)` | 测试是否通过必须真实运行 |

不好的工具：

| 不好的工具 | 问题 |
| --- | --- |
| `summarize_text(text)` | 模型自己就能总结 |
| `explain_concept(topic)` | 普通概念解释不需要工具 |
| `score_advisor(score)` | 太像简单规则，工具感不强 |

对应 Day 4：

```text
Tool Calling 模式 = app.py 把 tools.py 里的工具暴露给模型。
```

---

## 6. Harness：Agent 外面的工程系统

Harness 是今天最重要的概念。

一句话：

```text
Agent = Model + Harness
```

模型只是生成文本。  
Harness 才负责把模型接到真实工程环境里。

Harness 通常负责：

- 准备 Prompt
- 组织 Context
- 暴露工具
- 执行工具
- 保存状态
- 读取文件
- 写入文件
- 运行命令
- 管理权限
- 记录日志
- 处理错误
- 控制循环次数
- 判断什么时候停止

Day 4 项目就是一个很小的 Harness：

| 文件 | 作用 |
| --- | --- |
| `app.py` | 页面、模式选择、流程分发 |
| `llm_client.py` | 调用模型 API |
| `rag.py` | 准备 RAG 上下文 |
| `tools.py` | 定义工具和执行工具 |
| `.env` | 配置模型地址和模型名 |

所以这个项目不是：

```text
只有一个模型
```

而是：

```text
模型 + Prompt + Context + Tools + Gradio + Python 调度代码
```

这就是最小版 Harness。

---

## 7. Harness 的分层理解

可以把 Harness 分成几层看。

### 7.1 基础能力层

系统必须先具备一些基础能力：

- 调模型
- 读文件
- 写文件
- 发 HTTP 请求
- 调用工具
- 记录日志
- 捕获错误
- 控制权限

没有这些能力，就谈不上 Agent。

### 7.2 运行框架层

这一层决定系统怎么运行。

例如：

- Gradio 页面
- 命令行程序
- Web 服务
- IDE 插件
- Agent Framework

Day 4 用的是：

```text
Gradio + Python
```

### 7.3 设计组件层

这一层决定系统有哪些可组合组件。

例如：

- Chat
- RAG
- Tool Calling
- 状态管理
- 权限确认
- 错误处理
- 结果展示

Day 4 的模式切换，其实就是在切换不同组件组合。

### 7.4 Pattern 层

Pattern 是可复用的系统模式。

例如：

- RAG 问答
- 工具调用
- 先检索再回答
- 先计划再执行
- 失败后 fallback
- Loop
- Multi-agent

Loop 不是所有 Agent 的必需品。  
它是 Harness 上的一种 Pattern。

### 7.5 具体项目层

最后才是某个具体应用。

例如：

- 课程问答助手
- 天气出行助手
- 实验报错诊断助手
- 论文阅读助手
- 代码修改 Agent

不要一上来就问“我要不要做 Agent”。  
应该先问：

```text
我的项目需要哪些基础能力？
需要哪些上下文？
需要哪些工具？
流程是固定的，还是需要模型决定下一步？
需不需要循环？
```

---

## 8. Workflow：固定步骤的系统

Workflow 是固定步骤。

例子：

```text
用户问题
-> 检索知识库
-> 拼接上下文
-> 调用模型
-> 返回答案和来源
```

再例如：

```text
用户问题
-> 判断是否需要工具
-> 调用工具
-> 把工具结果交给模型
-> 返回最终回答
```

Workflow 的优点：

- 稳定
- 好调试
- 容易演示
- 失败位置清楚
- 适合课程项目

Workflow 的缺点：

- 不够灵活
- 步骤必须提前设计
- 遇到开放目标时能力有限

对 Day 6 来说：

```text
一个稳定 Workflow 通常比一个不稳定 Agent 更适合演示。
```

---

## 9. Loop：让系统自己继续

Loop 解决的是：

```text
系统完成一步后，如何根据结果继续下一步。
```

没有 Loop：

```text
用户问一次
-> 模型答一次
-> 结束
```

有 Loop：

```text
观察
-> 判断
-> 行动
-> 验证
-> 再观察
-> 再行动
-> 直到完成或停止
```

编程工具里的 Loop：

```text
读需求
-> 搜代码
-> 改文件
-> 跑测试
-> 读报错
-> 再改
-> 再测试
-> 总结
```

Loop 需要三类能力：

| 能力 | 含义 |
| --- | --- |
| Self-triggering | 系统能自动触发下一步 |
| Self-prompting | 系统能为下一步生成提示 |
| State persistence | 系统能保存上一步的状态 |

Loop 的价值：

- 不需要用户每一步都手动推动
- 可以根据失败结果调整策略
- 适合代码修复、长任务、自动排查

Loop 的风险：

- 可能死循环
- 可能越改越错
- 更难调试
- 需要停止条件
- 需要权限控制

所以：

```text
Loop 是优化，不是必需。
```

---

## 10. Agent：模型参与下一步决策

Agent 不是一个魔法词。

可以这样理解：

```text
Agent = 模型 + Harness + 可选择的工具 + 状态 + 决策逻辑
```

Agent 和 Workflow 的区别：

| 问题 | Workflow | Agent |
| --- | --- | --- |
| 步骤是否固定 | 固定 | 可以变化 |
| 下一步谁决定 | 程序 | 模型参与决定 |
| 是否容易调试 | 容易 | 更难 |
| 是否适合课堂演示 | 适合 | 要谨慎 |
| 是否需要状态 | 少量 | 更多 |
| 是否需要停止条件 | 简单 | 必须明确 |

Agent 适合：

- 目标开放
- 步骤不固定
- 中途需要根据结果调整
- 需要多次工具调用
- 需要长期状态

Agent 不适合：

- 简单问答
- 固定业务流程
- 模型能力不稳定
- 没有权限控制
- 没有日志和停止条件

课堂项目建议：

```text
先做好 Workflow。
如果项目已经稳定，再解释其中哪些地方有 Agent 思想。
```

---

## 11. Coding Agent：编程工具为什么变强

现在的 AI 编程工具不只是“帮你写代码”。

它们通常有这些能力：

- 读代码库
- 搜索文件
- 修改文件
- 运行命令
- 运行测试
- 读取报错
- 查看 git diff
- 根据测试结果继续修改
- 请求用户确认高风险操作

把前面的概念串起来：

| 阶段 | 编程场景 |
| --- | --- |
| Prompt | “帮我写一个函数” |
| Context | “根据这个文件修改函数” |
| Tool | “帮我搜索代码并运行测试” |
| Harness | “在项目目录里读写文件、执行命令、记录结果” |
| Workflow | “固定流程：读文件 -> 改代码 -> 跑测试” |
| Loop | “测试失败后继续读报错再修” |
| Agent | “模型参与决定下一步该搜代码、改文件还是跑测试” |

编程 Agent 的核心不是模型会不会写代码，而是：

```text
能不能看见项目
能不能行动
能不能验证
能不能根据验证结果继续
能不能安全地停下来
```

---

## 12. 常见误区

### 12.1 误区一：Prompt 写得好就够了

不够。

Prompt 只能改善表达方式，不能让模型获得真实世界状态。

如果问题需要当前时间、天气、文件、数据库或测试结果，就需要 Context 或 Tool。

### 12.2 误区二：用了工具就是 Agent

不是。

Tool Calling 只是让模型能调用外部能力。  
如果流程仍然是固定的，它更像 Workflow。

### 12.3 误区三：有 Loop 才叫 Agent

不一定。

Loop 是一种 Pattern。  
有些 Agent 不需要复杂 Loop，有些 Workflow 也可以包含简单 Loop。

### 12.4 误区四：Agent 越自主越好

不是。

越自主，越需要：

- 日志
- 权限
- 超时
- 停止条件
- 错误恢复
- 用户确认

没有这些，Agent 只会更难控。

### 12.5 误区五：模型更强就不用工程设计

不是。

模型变强会减少一些问题，但不会替代 Harness。

文件、工具、权限、状态、日志、验证，这些仍然需要工程系统管理。

---

## 13. 用这套框架看 Day 4 项目

Day 4 项目可以这样拆：

| 组件 | 对应概念 |
| --- | --- |
| System Prompt | Prompt |
| `data/kb.md` | Context |
| `rag.py` | Context Engineering |
| `tools.py` | Tool |
| `app.py` | Harness |
| Gradio 页面 | Harness 的交互层 |
| Tool Calling 模式 | Workflow + Tool |
| RAG 模式 | Workflow + Context |
| `.env` | Harness 配置 |

它还不是完整 Agent，因为：

- 没有复杂状态管理
- 没有长期记忆
- 没有自动循环
- 没有让模型长期规划多步任务

但它已经具备 Agent 系统的基础部件：

```text
模型
+ Prompt
+ Context
+ Tool
+ Harness
```

---

## 14. 用这套框架看自己的项目

为 Day 6 汇报准备时，先回答这几个问题。

### 14.1 你的项目主要解决什么问题？

```text
项目名称：
目标用户：
解决的问题：
```

### 14.2 你的项目用了哪些概念？

```text
Prompt：
Context：
Tool：
Harness：
Workflow：
Loop：
Agent：
```

不是每一项都必须有。  
没有就写“没有”。

### 14.3 你的项目为什么需要大模型？

不要只说“因为用了 AI”。

可以从这些角度说：

- 需要自然语言理解
- 需要生成解释
- 需要基于资料回答
- 需要把工具结果组织成人话
- 需要处理开放问题

### 14.4 你的项目哪里不是 Agent？

这个问题很重要。

能说清限制，说明你真的理解系统。

例子：

```text
本项目主要是 RAG Workflow，不是完整 Agent。
它的步骤是固定的：检索资料 -> 拼接 Prompt -> 调模型 -> 返回答案。
```

---

## 15. Day 6 演示准备

准备三个问题。

### 15.1 问题一：基础能力

证明页面和模型能正常工作。

```text
请用三句话介绍这个系统能做什么。
```

### 15.2 问题二：核心能力

展示项目最重要的能力。

RAG 项目示例：

```text
请根据课程资料回答：如何把 Python 函数接入 Tool Calling？
```

Tool Calling 项目示例：

```text
请查询 Asia/Shanghai 当前时间，并根据时间给一句提醒。
```

### 15.3 问题三：边界情况

展示系统不会乱编。

```text
如果资料里没有答案，请说明不知道，不要编造。
```

或者：

```text
请查询一个不存在的工具。
```

---

## 16. 演示脚本模板

```text
项目名称：

一句话介绍：

主要能力：
Chat / RAG / Tool Calling / Workflow / Agent 思想

系统拆解：
Prompt：
Context：
Tool：
Harness：
Workflow：
Loop：

演示问题 1：
预期结果：

演示问题 2：
预期结果：

演示问题 3：
预期结果：

如果现场失败：
备用问题：
备用截图：
```

---

## 17. 轻量完善建议

今天不强制新增功能。  
如果还有时间，优先做低风险修改。

| 优先级 | 修改项 | 原因 |
| --- | --- | --- |
| 高 | 改页面标题 | 让项目不像通用 Demo |
| 高 | 准备 3 个演示问题 | 避免现场临时想 |
| 高 | 改 System Prompt | 让回答贴合项目 |
| 中 | 整理 `data/kb.md` | RAG 项目需要资料质量 |
| 中 | 保留工具调用记录 | Tool Calling 项目需要证据 |
| 低 | 美化页面 | 稳定性更重要 |
| 低 | 新增复杂功能 | 容易影响演示 |

---

## 18. 常见演示风险

| 风险 | 处理方式 |
| --- | --- |
| Ollama 没启动 | 先运行 `ollama serve` |
| 端口不一致 | 检查 `.env` |
| 模型不存在 | 运行 `ollama list` |
| RAG 检索不到 | 检查 `data/kb.md` 关键词 |
| Tool Calling 没触发 | 问题写得更直接 |
| 页面打不开 | 看 `python app.py` 报错 |
| 模型回答慢 | 换短问题，降低上下文 |

---

## 19. 今天要记住

```text
Prompt：怎么问
Context：给它看什么
Tool：让它做什么
Harness：谁来组织这一切
Workflow：固定步骤
Loop：观察结果后继续
Agent：模型参与下一步决策
```

对 Day 6 来说：

```text
讲清楚一个稳定的小系统，比临时堆一个不稳定的 Agent 更重要。
```
