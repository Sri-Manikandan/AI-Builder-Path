import ollama
from vector_store import search

CHAT_MODEL = "llama3.2"


def answer(question: str) -> str:
    chunks = search(question)
    context = "\n\n".join(chunks)
    response = ollama.chat(
        model=CHAT_MODEL,
        messages=[
            
            {
                "role": "system",
                "content": (
                    "You are a helpful assistant. Answer the user's question using only "
                    "the provided context. If the answer is not in the context, say 'I don't know based on the provided document.'"
                    f"\n\nContext:\n{context}"
                ),
            },
            {"role": "user", "content": question},
        ],
    )
    return response.message.content


def chat_loop():
    print("\nAsk questions about your document. Type 'exit' to quit.\n")
    while True:
        question = input("You: ").strip()
        if not question:
            continue
        if question.lower() in ("exit", "quit"):
            print("Goodbye!")
            break
        print(f"\nAssistant: {answer(question)}\n")
