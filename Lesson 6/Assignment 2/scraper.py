"""Core web-scraping logic for the `web_scrape` tool.

This module is deliberately free of any AWS or LLM dependency so it can be
unit-tested on its own. It fetches a page, follows redirects, transparently
decodes gzip, enforces a byte-size limit, and returns cleaned plain text.
"""

from __future__ import annotations

import requests
from bs4 import BeautifulSoup

# --- Limits -----------------------------------------------------------------
MAX_BYTES = 2_000_000        # stop downloading after ~2 MB
MAX_REDIRECTS = 5            # cap redirect chains
MAX_SNIPPET_CHARS = 8_000    # trim the cleaned text returned to the agent
REQUEST_TIMEOUT = 15         # seconds

_HEADERS = {
    # A realistic UA avoids trivial bot-blocks; Accept-Encoding lets requests
    # negotiate + transparently decode gzip/deflate for us.
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0 Safari/537.36 WebCrawlerAgent/1.0"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate",
}


class ScrapeError(Exception):
    """Raised when a page cannot be fetched or is not scrapable."""


def _clean_html(html: str) -> str:
    """Strip markup/scripts and collapse whitespace into readable text."""
    soup = BeautifulSoup(html, "html.parser")

    # Drop non-content elements entirely.
    for tag in soup(["script", "style", "noscript", "template", "svg"]):
        tag.decompose()

    text = soup.get_text(separator="\n")

    # Collapse runs of blank lines / trailing spaces.
    lines = [line.strip() for line in text.splitlines()]
    cleaned = "\n".join(line for line in lines if line)
    return cleaned


def web_scrape(url: str) -> dict:
    """Fetch `url` and return a cleaned plain-text snippet.

    Returns a dict with either:
        {"url", "title", "text", "truncated", "bytes"}   on success
        {"url", "error"}                                  on failure
    """
    if not url or not url.lower().startswith(("http://", "https://")):
        return {"url": url, "error": "URL must start with http:// or https://"}

    session = requests.Session()
    session.max_redirects = MAX_REDIRECTS

    try:
        # stream=True so we can enforce the size cap before reading it all.
        resp = session.get(
            url,
            headers=_HEADERS,
            timeout=REQUEST_TIMEOUT,
            stream=True,
            allow_redirects=True,
        )
        resp.raise_for_status()

        content_type = resp.headers.get("Content-Type", "").lower()
        if content_type and "html" not in content_type and "text" not in content_type:
            return {
                "url": resp.url,
                "error": f"Unsupported content type: {content_type or 'unknown'}",
            }

        # Read up to MAX_BYTES; requests transparently un-gzips the stream.
        chunks = bytearray()
        truncated = False
        for chunk in resp.iter_content(chunk_size=16_384):
            chunks.extend(chunk)
            if len(chunks) >= MAX_BYTES:
                truncated = True
                break

        encoding = resp.encoding or "utf-8"
        html = chunks.decode(encoding, errors="replace")

    except requests.exceptions.TooManyRedirects:
        return {"url": url, "error": f"Exceeded {MAX_REDIRECTS} redirects"}
    except requests.exceptions.Timeout:
        return {"url": url, "error": f"Request timed out after {REQUEST_TIMEOUT}s"}
    except requests.exceptions.RequestException as exc:
        return {"url": url, "error": f"Fetch failed: {exc}"}
    finally:
        session.close()

    soup_title = BeautifulSoup(html, "html.parser").title
    title = soup_title.string.strip() if soup_title and soup_title.string else ""

    text = _clean_html(html)
    if len(text) > MAX_SNIPPET_CHARS:
        text = text[:MAX_SNIPPET_CHARS]
        truncated = True

    return {
        "url": resp.url,
        "title": title,
        "text": text,
        "truncated": truncated,
        "bytes": len(chunks),
    }


if __name__ == "__main__":
    import json
    import sys

    target = sys.argv[1] if len(sys.argv) > 1 else "https://example.com"
    print(json.dumps(web_scrape(target), indent=2)[:2000])
