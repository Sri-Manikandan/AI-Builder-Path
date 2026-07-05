"""Local stand-in for the Bedrock Agent runtime.

A real Bedrock Agent would: receive the user message, decide (via its
foundation model) whether to call the `web_scrape` action group, invoke the
Lambda, feed the tool result back to the model, and return a final answer.

We reproduce that loop locally with OpenAI function-calling. The tool schema
mirrors the Bedrock action group, and the tool invocation goes through the same
`lambda_handler` you would deploy.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from lambda_handler import lambda_handler

# Reuse the credentials from Lesson 6 / Assignment 1 (OPENAI_API_KEY etc.),
# falling back to a local .env if present.
_ASSIGNMENT1_ENV = Path(__file__).resolve().parent.parent / "Assignment 1" / ".env"
if _ASSIGNMENT1_ENV.exists():
    load_dotenv(_ASSIGNMENT1_ENV)
load_dotenv()  # local .env overrides / fills gaps

MODEL = os.getenv("AGENT_MODEL", "gpt-4o")

SYSTEM_PROMPT = """You are a Web Crawler Agent.

When the user asks you to crawl, scrape, read, or summarize a web page, call the
`web_scrape` tool with the URL. Then answer the user's question using only the
returned text. If the tool returns an error, explain the problem plainly and do
not invent content. Keep answers concise and cite the page title when available.
"""

# Mirrors the Bedrock action-group function definition.
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "web_scrape",
            "description": (
                "Fetch a web page and return its cleaned plain-text content. "
                "Handles redirects, gzip, and large pages. Use this whenever the "
                "user provides a URL to crawl, scrape, read, or summarize."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The absolute http(s) URL to fetch.",
                    }
                },
                "required": ["url"],
            },
        },
    }
]


def _invoke_tool(url: str) -> str:
    """Call the Lambda handler with a Bedrock-shaped event and unwrap the result."""
    event = {
        "actionGroup": "web-scraper",
        "function": "web_scrape",
        "parameters": [{"name": "url", "type": "string", "value": url}],
        "messageVersion": "1.0",
    }
    response = lambda_handler(event)
    body = response["response"]["functionResponse"]["responseBody"]["TEXT"]["body"]
    return body  # JSON string produced by the scraper


def run_agent(user_message: str, history: list[dict] | None = None):
    """Run one agent turn. Yields (event_type, payload) tuples for the UI.

    event types:
        "tool_call"  -> {"url": ...}
        "tool_result"-> parsed scraper dict
        "answer"     -> final assistant text
    """
    client = OpenAI()

    messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    # Allow a couple of tool rounds in case multiple URLs are requested.
    for _ in range(4):
        completion = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
            temperature=0,
        )
        msg = completion.choices[0].message

        if not msg.tool_calls:
            yield ("answer", msg.content or "")
            return

        # Record the assistant's tool-call turn.
        messages.append(
            {
                "role": "assistant",
                "content": msg.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in msg.tool_calls
                ],
            }
        )

        for tc in msg.tool_calls:
            args = json.loads(tc.function.arguments or "{}")
            url = args.get("url", "")
            yield ("tool_call", {"url": url})

            body = _invoke_tool(url)
            yield ("tool_result", json.loads(body))

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": body,
                }
            )

    yield ("answer", "Stopped after too many tool calls. Please refine your request.")


if __name__ == "__main__":
    import sys

    q = " ".join(sys.argv[1:]) or "Crawl this URL: https://example.com and summarize it."
    for kind, payload in run_agent(q):
        if kind == "tool_call":
            print(f"[tool] web_scrape({payload['url']})")
        elif kind == "tool_result":
            print(f"[result] {payload.get('title', '')} "
                  f"({payload.get('bytes', 0)} bytes)")
        else:
            print(f"\n{payload}")
