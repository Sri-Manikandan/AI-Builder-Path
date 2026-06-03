from langchain.tools import tool
from langchain_community.tools.tavily_search import TavilySearchResults

_tavily = TavilySearchResults(max_results=3)


@tool("web_search")
def web_search(query: str) -> str:
    """Search the web for current information: industry benchmarks, regulatory updates, market trends, and anything not in internal documents."""
    try:
        results = _tavily.invoke(query)
        if not results:
            return "No web search results found."
        return "\n\n---\n\n".join(
            f"Source: {r.get('url', 'N/A')}\n{r.get('content', '')}"
            for r in results
        )
    except Exception as e:
        return f"Web search error: {str(e)}"
