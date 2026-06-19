"""CLI for the multi-agent support system."""

from dotenv import load_dotenv

load_dotenv()

from src.graph import build_graph

_LABELS = {"it": "IT Agent", "finance": "Finance Agent"}


def main():
    graph = build_graph()
    print("Presidio Multi-Agent Support System ready. Type 'quit' to exit.\n")
    while True:
        query = input("Query: ").strip()
        if query.lower() in ("quit", "exit", "q"):
            break
        if not query:
            continue

        result = graph.invoke({"messages": [{"role": "user", "content": query}]})
        agent = _LABELS.get(result["category"], result["category"])
        answer = result["messages"][-1].content
        print(f"\n[Routed to: {agent}]")
        print(f"Answer: {answer}\n")


if __name__ == "__main__":
    main()
