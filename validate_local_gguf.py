import json

from llama_cpp import Llama

MODEL_PATH = "models/qwen2.5-0.5b-instruct-q4_k_m.gguf"


def main() -> None:
    llm = Llama(model_path=MODEL_PATH, n_ctx=2048, n_threads=4)
    messages = [
        {
            "role": "system",
            "content": (
                "Responde solo JSON válido con las claves role_test y answer."
            ),
        },
        {"role": "assistant", "content": "Entendido."},
        {
            "role": "user",
            "content": "Devuelve un JSON con role_test=true y answer='ok'.",
        },
    ]
    response = llm.create_chat_completion(
        messages=messages,
        temperature=0,
        max_tokens=128,
        response_format={"type": "json_object"},
    )
    content = (response["choices"][0]["message"]["content"] or "").strip()
    if not content:
        raise ValueError(f"Empty response content: {response}")
    data = json.loads(content)
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
