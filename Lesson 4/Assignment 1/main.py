from dotenv import load_dotenv
load_dotenv()

from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from tools.rag_tool import search_hr_policies
from tools.google_docs_tool import search_google_docs
from tools.web_search_tool import web_search

_SYSTEM_PROMPT = """You are Presidio's Internal Research Agent. You have access to three tools:

1. search_hr_policies: Search internal HR policy documents. Use for policies, compliance rules, hiring guidelines, and internal procedures.
2. search_google_docs: Search Presidio's Google Drive. Use for campaign data, reports, meeting notes, and company-specific internal documents.
3. web_search: Search the web. Use for industry benchmarks, regulatory updates, market trends, and external data.

Always reason about which tool(s) to use before acting. Use multiple tools when the query needs both internal and external data."""


def build_agent():
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    tools = [search_hr_policies, search_google_docs, web_search]
    return create_agent(model=llm, tools=tools, system_prompt=_SYSTEM_PROMPT)


def main():
    executor = build_agent()
    print("Presidio Internal Research Agent ready. Type 'quit' to exit.\n")
    while True:
        query = input("Query: ").strip()
        if query.lower() in ("quit", "exit", "q"):
            break
        if not query:
            continue
        result = executor.invoke({"messages": [{"role": "user", "content": query}]})
        print(f"\nAnswer: {result['messages'][-1].content}\n")


if __name__ == "__main__":
    main()
