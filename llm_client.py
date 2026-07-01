import os
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

# 读取 .env 文件里的 OPENAI_BASE_URL、MODEL 等配置。
# Ollama 提供 OpenAI 兼容接口，所以这里可以直接复用 openai SDK。
load_dotenv()

BASE_URL = os.getenv("OPENAI_BASE_URL", "http://127.0.0.1:11434/v1")
API_KEY = os.getenv("OPENAI_API_KEY", "ollama")
MODEL = os.getenv("MODEL", "Qwen3-1.7B-Q4_K_M")

# 这个 client 是全项目共用的模型客户端。
client = OpenAI(base_url=BASE_URL, api_key=API_KEY)


def chat_completion(
    messages: list[dict[str, Any]],
    temperature: float = 0.2,
    tools: list[dict[str, Any]] | None = None,
    tool_choice: str | dict[str, Any] | None = None,
):
    """统一封装一次聊天补全请求，Chat、RAG、Tool Calling 都走这里。"""
    kwargs: dict[str, Any] = {
        "model": MODEL,
        "messages": messages,
        "temperature": temperature,
    }

    # 只有 Tool Calling 模式需要传 tools 和 tool_choice。
    if tools is not None:
        kwargs["tools"] = tools
    if tool_choice is not None:
        kwargs["tool_choice"] = tool_choice

    return client.chat.completions.create(**kwargs)


def get_assistant_text(response) -> str:
    """从 OpenAI 兼容响应里取出 assistant 的文本内容。"""
    message = response.choices[0].message
    return message.content or ""