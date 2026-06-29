from llm_client import BASE_URL, MODEL, client


def main():
    print(f"Checking Ollama OpenAI-compatible API: {BASE_URL}")
    print(f"Model: {MODEL}")

    models = client.models.list()
    model_names = [item.id for item in models.data]
    print("Available models:")
    for name in model_names:
        print(f"- {name}")

    if MODEL not in model_names:
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
