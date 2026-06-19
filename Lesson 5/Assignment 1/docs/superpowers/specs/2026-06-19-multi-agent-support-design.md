# Multi-Agent Support System — Design

**Date:** 2026-06-19
**Assignment:** Lesson 5 / Assignment 1 — Multi-Agent Support System using LangGraph

## Goal

Build a multi-agent support system that classifies user queries as **IT** or
**Finance** and routes them to the appropriate specialist agent. Each specialist
answers using internal documents (`ReadFile`) and external web data (`WebSearch`).

## Architecture

A LangGraph `StateGraph` in a supervisor pattern:

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

### State

```python
class SupportState(TypedDict):
    messages: Annotated[list, add_messages]
    category: str  # "it" | "finance"
```

### Components

| File | Responsibility |
| --- | --- |
| `src/tools.py` | `read_it_docs`, `read_finance_docs` (read local markdown), shared `web_search` (Tavily) |
| `src/supervisor.py` | Single gpt-4o classification call returning exactly `it` or `finance` |
| `src/agents.py` | Two ReAct specialist agents via `create_react_agent`, each with its tools + domain prompt |
| `src/graph.py` | Assembles supervisor + conditional edges + specialists into compiled graph |
| `main.py` | CLI loop; prints routed agent then the answer |

### Tools

- **ReadFile** — `read_it_docs(query)` / `read_finance_docs(query)` read and
  concatenate markdown from `docs/it/` and `docs/finance/`. Simple file reads,
  no vector DB.
- **WebSearch** — Tavily-backed `web_search(query)`, reused pattern from Lesson 4.

### Specialist agents

Each is a full tool-using ReAct agent so it decides on its own whether to consult
internal docs, the web, or both. System prompts instruct: prefer internal docs
for policy/procedure questions; use web search for public/external data.

### Supervisor

A minimal classifier: one gpt-4o call with a strict prompt returning `it` or
`finance`. Output is normalized (lowercased, stripped) and defaults to `it` if
ambiguous. No tools.

## Sample data

- `docs/it/`: VPN setup, approved software, laptop request process
- `docs/finance/`: reimbursement filing, budget reports, payroll schedule

Lets the assignment's example queries work out of the box.

## Config & tooling

- LLM: OpenAI `gpt-4o` (reuses existing `OPENAI_API_KEY`).
- `.env` for `OPENAI_API_KEY`, `TAVILY_API_KEY`.
- `requirements.txt`: langgraph, langchain-openai, tavily-python, python-dotenv.
- `.gitignore`: `.env`, `.venv/`, `__pycache__/`, `*.pyc`.

## Error handling

- Missing API keys -> clear startup error.
- Empty/missing doc folder -> tool returns a "no documents found" message rather
  than crashing.
- Supervisor non-matching output -> defaults to `it`.

## Out of scope (YAGNI)

- Vector/RAG search, persistence, web UI, multi-turn memory across sessions.
