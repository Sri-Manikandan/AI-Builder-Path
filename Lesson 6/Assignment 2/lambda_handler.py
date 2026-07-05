"""AWS Lambda handler that backs the Bedrock Agent `web_scrape` action group.

This is the exact function you would deploy to Lambda. Bedrock invokes it with
an action-group event and expects a specific `response` envelope back. Locally,
`agent.py` calls `lambda_handler` directly to simulate the Bedrock -> Lambda hop,
so the same code works in both worlds.

Bedrock action-group event shape (simplified):
{
  "actionGroup": "web-scraper",
  "function": "web_scrape",
  "parameters": [{"name": "url", "type": "string", "value": "https://..."}],
  "messageVersion": "1.0"
}
"""

from __future__ import annotations

import json

from scraper import web_scrape


def _get_param(event: dict, name: str) -> str | None:
    """Pull a named parameter out of a Bedrock action-group event."""
    for param in event.get("parameters", []) or []:
        if param.get("name") == name:
            return param.get("value")
    return None


def lambda_handler(event: dict, context=None) -> dict:
    """Entry point invoked by the Bedrock Agent runtime."""
    action_group = event.get("actionGroup", "web-scraper")
    function = event.get("function", "web_scrape")

    url = _get_param(event, "url")
    result = web_scrape(url)

    # Bedrock expects the tool result as a JSON string in responseBody.
    response_body = {"TEXT": {"body": json.dumps(result)}}

    return {
        "messageVersion": event.get("messageVersion", "1.0"),
        "response": {
            "actionGroup": action_group,
            "function": function,
            "functionResponse": {"responseBody": response_body},
        },
    }
