# 🕷️ Web Crawler Agent (AWS Bedrock — local simulation)

A Web Crawler Agent that mirrors the **AWS Bedrock Agent → action group → Lambda scraper**
architecture, run entirely locally. Ask it to crawl a URL and it fetches, cleans,
and summarizes the page.

## Architecture

```
Streamlit UI  ──user msg──►  Agent runtime  ──tool call──►  Lambda handler  ──►  Scraper
  (app.py)                    (agent.py)       web_scrape     (lambda_handler.py)  (scraper.py)
      ▲                            │                                  │
      └──────── final answer ◄─────┴──────────── cleaned text ◄───────┘
```

| File | Role | Real Bedrock equivalent |
|------|------|-------------------------|
| `scraper.py` | Fetch + clean HTML (redirects, gzip, size cap) | Business logic inside the Lambda |
| `lambda_handler.py` | Parses the Bedrock action-group event, returns the `functionResponse` envelope | The deployed **Lambda function** |
| `agent.py` | LLM tool-use loop; registers `web_scrape` and invokes the handler | The **Bedrock Agent runtime** + agent alias |
| `app.py` | Streamlit chat frontend | Your web frontend |

`agent.py` uses OpenAI function-calling as the agent's reasoning brain. The
`web_scrape` tool schema and the Lambda event/response shapes match Bedrock's
contract, so `lambda_handler.py` is deployable to a real Lambda + action group
with no code changes.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Credentials are reused from `../Assignment 1/.env` (needs `OPENAI_API_KEY`).
Optionally set `AGENT_MODEL` (default `gpt-4o`).

## Run

**Frontend (recommended):**
```bash
streamlit run app.py
```

**CLI:**
```bash
python agent.py "Crawl this URL: https://example.com and summarize it."
```

**Scraper only:**
```bash
python scraper.py https://example.com
```

## The `web_scrape` tool

Fetches an `http(s)` URL and returns cleaned plain text. It:
- follows redirects (capped at 5),
- transparently decodes gzip/deflate,
- enforces a ~2 MB download cap and an 8k-char snippet cap (`truncated` flag),
- rejects non-HTML content types and malformed URLs,
- returns structured errors (timeouts, too many redirects, fetch failures)
  instead of crashing.

## Deploying to real AWS Bedrock (optional)

The local structure maps 1:1 to a real deployment:
1. Zip `scraper.py` + `lambda_handler.py` (with `requests`/`bs4` in a layer) and deploy as a Lambda.
2. Create a Bedrock Agent; add an **action group** with function `web_scrape` (param `url`) pointing at the Lambda.
3. Create an **agent alias**.
4. Point the frontend at the Bedrock Agent runtime (`bedrock-agent-runtime:InvokeAgent`) instead of the local `run_agent`.
