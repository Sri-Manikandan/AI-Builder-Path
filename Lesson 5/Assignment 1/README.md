# Multi-Agent Support System (LangGraph)

A multi-agent support system built with **LangGraph**. A supervisor agent
classifies each query as **IT** or **Finance** and routes it to the matching
specialist agent. Each specialist answers using internal documents (`ReadFile`)
and the public web (`WebSearch`).

## Architecture

```
user query -> Supervisor (classify: it | finance)
                   |
        conditional routing
          /                \
     IT Agent          Finance Agent
   ReadFile+WebSearch  ReadFile+WebSearch
          \                /
                 END
```

- **Supervisor** (`src/supervisor.py`) — one gpt-4o call returning `it` or `finance`.
- **IT Agent** (`src/agents.py`) — ReAct agent with `read_it_docs` + `web_search`.
- **Finance Agent** (`src/agents.py`) — ReAct agent with `read_finance_docs` + `web_search`.
- **Graph** (`src/graph.py`) — wires supervisor + conditional edges + specialists.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file with these keys:

- `OPENAI_API_KEY` — for gpt-4o
- `TAVILY_API_KEY` — for web search

## Run

```bash
python main.py
```

Example queries:

- IT: `How to set up VPN?`, `What software is approved for use?`, `How to request a new laptop?`
- Finance: `How to file a reimbursement?`, `Where to find last month's budget report?`, `When is payroll processed?`

## Internal docs

Sample markdown lives in `docs/it/` and `docs/finance/`. Add your own `.md`
files there and the `ReadFile` tools will pick them up automatically.
