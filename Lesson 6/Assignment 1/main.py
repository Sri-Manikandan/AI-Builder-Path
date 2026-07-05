from dotenv import load_dotenv

load_dotenv()

from agent import build_agent
from guardrails import check_input, check_output
from observability import get_langfuse_handler


def run_query(agent, query: str, handler) -> str:
    allowed, reason = check_input(query)
    if not allowed:
        return f"[blocked by input guardrail] {reason}"

    config = {"callbacks": [handler]} if handler else {}
    result = agent.invoke({"messages": [{"role": "user", "content": query}]}, config=config)
    answer = result["messages"][-1].content

    allowed, safe_text = check_output(answer)
    if not allowed:
        return f"[blocked by output guardrail] {safe_text}"
    return safe_text


def main():
    agent = build_agent()
    handler = get_langfuse_handler()
    print("Presidio Internal Research Agent ready. Type 'quit' to exit.\n")
    while True:
        query = input("Query: ").strip()
        if query.lower() in ("quit", "exit", "q"):
            break
        if not query:
            continue
        print(f"\nAnswer: {run_query(agent, query, handler)}\n")


if __name__ == "__main__":
    main()
