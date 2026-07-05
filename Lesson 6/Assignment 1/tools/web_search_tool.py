import os

from langchain.tools import tool
from tavily import TavilyClient


@tool("web_search")
def web_search(query: str) -> str:
    """Search the web for current information: industry benchmarks, regulatory updates, market trends, and anything not in internal documents."""
    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        return "Web search unavailable: TAVILY_API_KEY is not set."
    try:
        client = TavilyClient(api_key=api_key)
        response = client.search(query=query, max_results=3)
        results = response.get("results", [])
        if not results:
            return "No web search results found."
        return "\n\n---\n\n".join(
            f"Source: {r.get('url', 'N/A')}\n{r.get('content', '')}"
            for r in results
        )
    except Exception as e:
        return f"Web search error: {str(e)}"
