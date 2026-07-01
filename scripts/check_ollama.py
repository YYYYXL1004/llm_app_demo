from pathlib import Path
import sys

# 允许学生直接运行 `python scripts/check_ollama.py`。
# 因为脚本在 scripts/ 子目录里，需要把项目根目录加入 Python 搜索路径。
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from llm_client import BASE_URL, MODEL, client


def main():
    """检查 Ollama 的 OpenAI 兼容接口、模型列表和一次最小聊天调用。"""
    print(f"Checking Ollama OpenAI-compatible API: {BASE_URL}")
    print(f"Model: {MODEL}")

    models = client.models.list()
    model_names = [item.id for item in models.data]
    print("Available models:")
    for name in model_names:
        print(f"- {name}")

    # Ollama 经常把模型显示为 `name:latest`，而 .env 里可能只写 `name`。
    # 这两种写法都可以调用，所以检查时要把 tag 去掉再比一次。
    normalized_model_names = {name.split(":", 1)[0] for name in model_names}
    if MODEL not in model_names and MODEL not in normalized_model_names:
        print(f"\nWarning: {MODEL} is not in the model list. Run: ollama list or check whether the model has been created.")

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": "用一句话回答：Ollama API 是否可用？"}],
        temperature=0,
    )
    print("\nChat test:")
    print(response.choices[0].message.content)


if __name__ == "__main__":
    main()