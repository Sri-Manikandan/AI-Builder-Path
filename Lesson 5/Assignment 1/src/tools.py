"""Tools for the specialist agents: ReadFile (internal docs) and WebSearch."""

import os
from pathlib import Path

from langchain_core.tools import tool
from tavily import TavilyClient

# docs/ lives at the project root, one level up from src/
_DOCS_ROOT = Path(__file__).resolve().parent.parent / "docs"


def _read_docs(folder: str, query: str) -> str:
    """Read and concatenate every markdown file in docs/<folder>."""
    doc_dir = _DOCS_ROOT / folder
    if not doc_dir.is_dir():
        return f"No documents found for '{folder}'."

    files = sorted(doc_dir.glob("*.md"))
    if not files:
        return f"No documents found for '{folder}'."

    sections = []
    for path in files:
        text = path.read_text(encoding="utf-8").strip()
        sections.append(f"=== {path.name} ===\n{text}")
    return "\n\n".join(sections)


@tool
def read_it_docs(query: str) -> str:
    """Read Presidio's internal IT documentation (VPN setup, approved software,
    laptop requests, etc.). Use this first for IT policy and procedure questions."""
    return _read_docs("it", query)


@tool
def read_finance_docs(query: str) -> str:
    """Read Presidio's internal Finance documentation (reimbursements, budget
    reports, payroll schedule, etc.). Use this first for Finance policy and
    procedure questions."""
    return _read_docs("finance", query)


@tool
def web_search(query: str) -> str:
    """Search the public web for external information not found in internal docs
    (industry standards, public regulations, market data, vendor documentation)."""
    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        return "Web search unavailable: TAVILY_API_KEY is not set."

    client = TavilyClient(api_key=api_key)
    response = client.search(query=query, max_results=3)
    results = response.get("results", [])
    if not results:
        return "No web results found."

    formatted = []
    for item in results:
        formatted.append(f"- {item.get('title', '')}: {item.get('content', '')}")
    return "\n".join(formatted)
