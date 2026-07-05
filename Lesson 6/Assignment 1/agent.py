from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from tools.rag_tool import search_hr_policies
from tools.web_search_tool import web_search

_SYSTEM_PROMPT = """You are Presidio's Internal Research Agent. You have access to two tools:

1. search_hr_policies: Search internal HR policy documents. Use for policies, compliance rules, hiring guidelines, and internal procedures.
2. web_search: Search the web. Use for industry benchmarks, regulatory updates, market trends, and external data.

Always reason about which tool(s) to use before acting. Use multiple tools when the query needs both internal and external data."""


def build_agent():
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    tools = [search_hr_policies, web_search]
    return create_react_agent(llm, tools=tools, prompt=_SYSTEM_PROMPT)
