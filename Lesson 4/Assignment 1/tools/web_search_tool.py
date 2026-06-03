from langchain.tools import tool
from langchain_tavily import TavilySearch

_tavily = TavilySearch(max_results=3)


@tool("web_search")
def web_search(query: str) -> str:
    """Search the web for current information: industry benchmarks, regulatory updates, market trends, and anything not in internal documents."""
    try:
        response = _tavily.invoke(query)
        results = response.get("results", []) if isinstance(response, dict) else []
        if not results:
            return "No web search results found."
        return "\n\n---\n\n".join(
            f"Source: {r.get('url', 'N/A')}\n{r.get('content', '')}"
            for r in results
        )
    except Exception as e:
        return f"Web search error: {str(e)}"
