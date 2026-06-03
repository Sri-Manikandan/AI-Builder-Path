from dotenv import load_dotenv
load_dotenv()

from langchain_openai import ChatOpenAI
from langchain.agents import create_react_agent, AgentExecutor
from langchain.prompts import PromptTemplate
from tools.rag_tool import search_hr_policies
from tools.google_docs_tool import search_google_docs
from tools.web_search_tool import web_search

_PROMPT_TEMPLATE = """You are Presidio's Internal Research Agent. You have access to three tools:

1. search_hr_policies: Search internal HR policy documents. Use for policies, compliance rules, hiring guidelines, and internal procedures.
2. search_google_docs: Search Presidio's Google Drive. Use for campaign data, reports, meeting notes, and company-specific internal documents.
3. web_search: Search the web. Use for industry benchmarks, regulatory updates, market trends, and external data.

Always reason about which tool(s) to use before acting. Use multiple tools when the query needs both internal and external data.

{tools}

Use the following format:
Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought:{agent_scratchpad}"""


def build_agent() -> AgentExecutor:
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    tools = [search_hr_policies, search_google_docs, web_search]
    prompt = PromptTemplate.from_template(_PROMPT_TEMPLATE)
    agent = create_react_agent(llm=llm, tools=tools, prompt=prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)


def main():
    executor = build_agent()
    print("Presidio Internal Research Agent ready. Type 'quit' to exit.\n")
    while True:
        query = input("Query: ").strip()
        if query.lower() in ("quit", "exit", "q"):
            break
        if not query:
            continue
        result = executor.invoke({"input": query})
        print(f"\nAnswer: {result['output']}\n")


if __name__ == "__main__":
    main()
