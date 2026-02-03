import os

from llama_cpp import Llama

MODEL_PATH = os.getenv(
    "MODEL_PATH", "models/qwen2.5-0.5b-instruct-q4_k_m.gguf"
)
N_CTX = int(os.getenv("N_CTX", "2048"))
N_THREADS = int(os.getenv("N_THREADS", "1"))


def run_test(llm: Llama, title: str, messages: list[dict[str, str]]) -> None:
    print(f"=== {title} ===")
    response = llm.create_chat_completion(
        messages=messages,
        temperature=0,
        max_tokens=128,
    )
    content = (response["choices"][0]["message"]["content"] or "").strip()
    print(content)
    print()


def main() -> None:
    llm = Llama(model_path=MODEL_PATH, n_ctx=N_CTX, n_threads=N_THREADS)
    tests: list[tuple[str, list[dict[str, str]]]] = [
        (
            "System role Q1",
            [
                {
                    "role": "system",
                    "content": "Responde en una oración: ¿Qué es un GGUF?",
                },
                {"role": "user", "content": "Responde ahora."},
            ],
        ),
        (
            "System role Q2",
            [
                {
                    "role": "system",
                    "content": "Responde en una oración: ¿Qué es llama-cpp?",
                },
                {"role": "user", "content": "Respuesta breve."},
            ],
        ),
        (
            "Assistant role Q1",
            [
                {
                    "role": "assistant",
                    "content": (
                        "Pregunta: ¿Qué beneficio tiene el riego por goteo?"
                    ),
                },
                {
                    "role": "user",
                    "content": "Responde la pregunta anterior en una oración.",
                },
            ],
        ),
        (
            "Assistant role Q2",
            [
                {
                    "role": "assistant",
                    "content": "Pregunta: ¿Qué es la rotación de cultivos?",
                },
                {
                    "role": "user",
                    "content": "Responde la pregunta anterior en una oración.",
                },
            ],
        ),
        (
            "User role Q1",
            [
                {
                    "role": "user",
                    "content": (
                        "¿Qué debo revisar si mi tomate tiene manchas amarillas?"
                    ),
                }
            ],
        ),
        (
            "User role Q2",
            [
                {
                    "role": "user",
                    "content": (
                        "Resume en una oración qué es el control biológico."
                    ),
                }
            ],
        ),
    ]

    for title, messages in tests:
        run_test(llm, title, messages)


if __name__ == "__main__":
    main()
