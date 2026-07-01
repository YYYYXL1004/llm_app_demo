import json
import os
from pathlib import Path
from typing import Any

import gradio as gr

from llm_client import BASE_URL, MODEL, chat_completion, get_assistant_text
from rag import KnowledgeBase, format_context
from tools import TOOL_SCHEMAS, run_tool

ROOT = Path(__file__).parent
KB = KnowledgeBase.from_markdown(ROOT / "data" / "kb.md")

DEFAULT_SYSTEM_PROMPT = """你是一个面向大学课堂的 LLM 应用助教。
回答要结构清晰、短而准确。
不知道时直接说明不知道，并给出下一步验证方法。
不要编造不存在的接口、论文、命令或运行结果。"""


def normalize_history(history: list[Any]) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = []
    for item in history or []:
        if isinstance(item, dict):
            role = item.get("role")
            content = item.get("content")
            if role in {"user", "assistant"} and isinstance(content, str):
                messages.append({"role": role, "content": content})
        elif isinstance(item, (list, tuple)) and len(item) == 2:
            user_msg, assistant_msg = item
            if user_msg:
                messages.append({"role": "user", "content": str(user_msg)})
            if assistant_msg:
                messages.append({"role": "assistant", "content": str(assistant_msg)})
    return messages[-8:]


def build_base_messages(system_prompt: str, history: list[Any]) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = [{"role": "system", "content": system_prompt or DEFAULT_SYSTEM_PROMPT}]
    messages.extend(normalize_history(history))
    return messages


def run_chat(message: str, history: list[Any], temperature: float, system_prompt: str) -> str:
    messages = build_base_messages(system_prompt, history)
    messages.append({"role": "user", "content": message})
    return get_assistant_text(chat_completion(messages, temperature=temperature))


def run_rag(message: str, history: list[Any], temperature: float, system_prompt: str, top_k: int) -> str:
    results = KB.search(message, top_k=top_k)
    context = format_context(results)
    messages = build_base_messages(system_prompt, history)
    messages.append(
        {
            "role": "user",
            "content": (
                "请只基于下面的课程资料回答问题。"
                "如果资料不足，请说明缺少什么信息。\n\n"
                f"{context}\n\n问题：{message}"
            ),
        }
    )
    answer = get_assistant_text(chat_completion(messages, temperature=temperature))
    refs = "\n".join([f"- {result.title}，score={result.score:.3f}" for result in results]) or "- 无"
    return f"{answer}\n\n检索到的资料：\n{refs}"


def run_tool_calling(message: str, history: list[Any], temperature: float, system_prompt: str) -> str:
    messages = build_base_messages(system_prompt, history)
    messages.append({"role": "user", "content": message})

    first = chat_completion(messages, temperature=temperature, tools=TOOL_SCHEMAS, tool_choice="auto")
    assistant_message = first.choices[0].message
    tool_calls = assistant_message.tool_calls or []

    if not tool_calls:
        return (assistant_message.content or "") + "\n\n说明：本次模型没有发起 tool call。可以换更强的模型，或改问需要精确计算、查时间、查已有 Python 函数状态的问题。"

    messages.append(assistant_message.model_dump(exclude_none=True))
    tool_logs = []

    for tool_call in tool_calls:
        name = tool_call.function.name
        try:
            arguments = json.loads(tool_call.function.arguments or "{}")
            result = run_tool(name, arguments)
        except Exception as exc:
            result = json.dumps({"error": str(exc)}, ensure_ascii=False)

        tool_logs.append(f"- {name}({tool_call.function.arguments}) -> {result}")
        messages.append(
            {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result,
            }
        )

    second = chat_completion(messages, temperature=temperature)
    answer = get_assistant_text(second)
    return f"{answer}\n\n工具调用记录：\n" + "\n".join(tool_logs)


def run_agent_fallback(message: str, history: list[Any], temperature: float, system_prompt: str, top_k: int) -> str:
    if len(message.strip()) < 6 or any(word in message for word in ["那个", "这个", "随便", "怎么弄"]):
        return "这个问题的信息不足。请补充目标、输入、期望输出和当前报错。课堂上这就是 Agent 的追问节点。"

    try:
        if any(word in message.lower() for word in ["计算", "time", "时间", "函数", "function", "工具"]):
            return run_tool_calling(message, history, temperature, system_prompt)
        return run_rag(message, history, temperature, system_prompt, top_k)
    except Exception as exc:
        return (
            "自动流程失败，已进入 fallback。\n\n"
            f"失败原因：{exc}\n\n"
            "可执行的下一步：检查模型服务是否可用、缩小问题范围、改用普通 Chat 模式、查看服务日志。"
        )


def respond(
    message: str,
    history: list[Any],
    mode: str,
    temperature: float,
    top_k: int,
    system_prompt: str,
) -> str:
    try:
        if mode == "RAG":
            return run_rag(message, history, temperature, system_prompt, top_k)
        if mode == "Tool Calling":
            return run_tool_calling(message, history, temperature, system_prompt)
        if mode == "Agent Fallback":
            return run_agent_fallback(message, history, temperature, system_prompt, top_k)
        return run_chat(message, history, temperature, system_prompt)
    except Exception as exc:
        return (
            f"调用失败：{exc}\n\n"
            f"当前 base_url={BASE_URL}, model={MODEL}。"
            "请先运行 `python scripts/check_ollama.py` 检查 Ollama 服务。"
        )


def build_demo():
    with gr.Blocks(title="LLM 应用基础 Demo", fill_height=True) as demo:
        gr.Markdown("# LLM 应用基础 Demo")
        gr.Markdown(f"当前模型：`{MODEL}`；API：`{BASE_URL}`")

        with gr.Row():
            mode = gr.Dropdown(
                choices=["Chat", "RAG", "Tool Calling", "Agent Fallback"],
                value="Chat",
                label="模式",
            )
            temperature = gr.Slider(0, 1.5, value=0.2, step=0.1, label="temperature")
            top_k = gr.Slider(1, 5, value=3, step=1, label="RAG top_k")

        system_prompt = gr.Textbox(
            value=DEFAULT_SYSTEM_PROMPT,
            lines=4,
            label="System Prompt",
        )

        gr.ChatInterface(
            fn=respond,
            additional_inputs=[mode, temperature, top_k, system_prompt],
            examples=[
                ["Prompt 为什么要写角色、任务和约束？", "Chat", 0.2, 3, DEFAULT_SYSTEM_PROMPT],
                ["如何把任意已有 Python 函数接入 Tool Calling？", "RAG", 0.2, 3, DEFAULT_SYSTEM_PROMPT],
                ["帮我计算 23*17+9，并告诉我 Asia/Shanghai 当前时间。", "Tool Calling", 0.1, 3, DEFAULT_SYSTEM_PROMPT],
                ["这个怎么弄？", "Agent Fallback", 0.2, 3, DEFAULT_SYSTEM_PROMPT],
            ],
            save_history=True,
        )
    return demo


if __name__ == "__main__":
    server_name = os.getenv("GRADIO_SERVER_NAME", "127.0.0.1")
    server_port = int(os.getenv("GRADIO_SERVER_PORT", "7860"))
    build_demo().queue().launch(server_name=server_name, server_port=server_port)
