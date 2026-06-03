# Presidio Internal Research Agent — Design Spec

**Date:** 2026-06-03  
**Assignment:** Lesson 4 — Assignment 1  
**Approach:** LangChain ReAct Agent with three tools

---

## Overview

An internal research agent for Presidio that routes queries to the right data source and synthesizes a final answer. Built with LangChain's ReAct agent pattern (`create_react_agent`), powered by OpenAI `gpt-4o`, with three specialized tools.

---

## Architecture

```
main.py
├── Agent: ReAct (create_react_agent)
│   ├── LLM: ChatOpenAI (gpt-4o)
│   └── Tools:
│       ├── tools/rag_tool.py         → RAG over hr_policies.pdf via ChromaDB
│       ├── tools/google_docs_tool.py → Google Docs API (OAuth credentials.json)
│       └── tools/web_search_tool.py  → Tavily search (replaces stub)
│
├── docs/
│   └── hr_policies.pdf              (pre-existing)
│
├── chroma_langchain_db/             (persisted vector store, auto-created on first run)
└── .env                             (OPENAI_API_KEY, TAVILY_API_KEY, GOOGLE_CREDENTIALS_PATH)
```

---

## Components

### `tools/rag_tool.py`
- Loads `docs/hr_policies.pdf` with `PyPDFLoader`
- Splits with `RecursiveCharacterTextSplitter` (chunk_size=1000, overlap=200)
- Ingests into the existing ChromaDB collection `presidio_collection` (skips if already populated)
- `@tool` function: similarity search, returns top-3 chunks as a formatted string

### `tools/google_docs_tool.py`
- Auth: `google-api-python-client` with `credentials.json` via OAuth
- `@tool` function: uses Drive API `fullText contains '<query>'` to list matching docs, fetches the first result's content (exported as plain text), returns trimmed text (max 3000 chars)
- Credentials path set via `GOOGLE_CREDENTIALS_PATH` in `.env`

### `tools/web_search_tool.py`
- Uses `TavilySearchResults` from `langchain_community.tools`
- Returns top-3 results for a given query
- Requires `TAVILY_API_KEY` in `.env`

### `main.py`
- Initializes all three tools
- Builds ReAct agent with a system prompt describing each tool's purpose and when to use it
- Runs an interactive query loop

---

## Data Flow

```
User Query
    │
    ▼
ReAct Agent (LLM reasons: which tool do I need?)
    │
    ├─► rag_tool("HR policy on X")
    │       └─ ChromaDB similarity search → top-3 chunks → string
    │
    ├─► google_docs_tool("Q1 marketing campaign feedback")
    │       └─ Drive list → fetch doc → trimmed text
    │
    └─► web_search_tool("AI data handling compliance 2025")
            └─ Tavily API → top-3 results → formatted string
    │
    ▼
LLM synthesizes all tool outputs → Final Answer
```

---

## Error Handling

| Tool | Failure Mode | Handling |
|---|---|---|
| RAG | Empty ChromaDB | Auto-ingests PDF before searching |
| Google Docs | API error / auth failure | Returns descriptive error string; agent continues |
| Web Search | Tavily API error | Returns descriptive error string; agent uses other tools |

All tools return `str` — the agent never raises on a tool failure.

---

## Environment Variables

| Variable | Purpose |
|---|---|
| `OPENAI_API_KEY` | OpenAI LLM + embeddings (already set) |
| `TAVILY_API_KEY` | Tavily web search API |
| `GOOGLE_CREDENTIALS_PATH` | Path to Google OAuth `credentials.json` |

---

## Sample Queries & Expected Tool Routing

| Query | Tools Used |
|---|---|
| "Summarize customer feedback from Q1 campaigns" | Google Docs → Web Search |
| "Compare our hiring trend with industry benchmarks" | RAG → Web Search |
| "Find compliance policies for AI data handling" | RAG → Web Search |

---

## Dependencies to Add

```
langchain
langchain-openai
langchain-community
langchain-chroma
tavily-python
pypdf
google-api-python-client
google-auth-oauthlib
python-dotenv
```
