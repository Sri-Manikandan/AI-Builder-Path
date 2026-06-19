"""Supervisor: classifies a query as IT or Finance."""

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

_CLASSIFY_PROMPT = """You are a routing supervisor for an internal support system.
Classify the user's query into exactly one category:

- "it"      -> IT topics: VPN, software, hardware/laptops, accounts, devices,
               security tools, technical support.
- "finance" -> Finance topics: reimbursements, expenses, budgets, payroll,
               invoices, taxes, financial reports.

Respond with ONLY one lowercase word: it OR finance. No punctuation, no
explanation."""


def classify(query: str) -> str:
    """Return 'it' or 'finance' for the given query. Defaults to 'it' if the
    model returns anything unexpected."""
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    response = llm.invoke(
        [SystemMessage(content=_CLASSIFY_PROMPT), HumanMessage(content=query)]
    )
    label = response.content.strip().lower()
    return "finance" if "finance" in label else "it"
