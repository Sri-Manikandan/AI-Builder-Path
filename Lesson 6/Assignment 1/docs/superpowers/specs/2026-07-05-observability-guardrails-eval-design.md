# LangFuse Observability + NeMo Guardrails + AgentEval — Design

**Date:** 2026-07-05
**Assignment:** Lesson 6 / Assignment 1 — Integrate LangFuse, Guardrails & Evaluate Your Agents

## Goal

Take the Lesson 4 "Presidio Internal Research Agent" (LangChain `create_agent`, tools:
HR-policy RAG search + web search) and, in a self-contained Lesson 6 copy:

1. Add LangFuse tracing capturing token usage, prompts, tool usage, and intermediate steps.
2. Wrap the agent with NeMo Guardrails input/output contracts.
3. Benchmark the agent with `agentevals` and document results in Markdown.

## Base agent (carried over from Lesson 4)

- `create_agent(model=ChatOpenAI(gpt-4o), tools=[search_hr_policies, web_search])`.
- `search_hr_policies`: Chroma-backed RAG over `docs/hr_policies.pdf` (`text-embedding-3-large`).
- `web_search`: Tavily-backed web search.
- The Google Docs tool from Lesson 4 is intentionally **dropped** — it requires an
  interactive OAuth consent flow, which is incompatible with running the eval
  benchmark non-interactively.

## Architecture

```
user query
   |
   v
guardrail input check (NeMo Guardrails, self-check-input rail)
   |  blocked? -> return refusal, agent never runs
   v
LangChain agent (LangFuse-traced: prompts, tokens, tool calls, steps)
   |
   v
guardrail output check (NeMo Guardrails, self-check-output rail)
   |  blocked? -> return refusal instead of raw answer
   v
final answer to user
```

The same pipeline (guardrail-in -> traced agent -> guardrail-out) is used both by
the interactive CLI (`main.py`) and the eval runner (`eval/run_eval.py`), so eval
runs produce real LangFuse traces and exercise the real guardrail contracts.

## File layout

```
Lesson 6/Assignment 1/
├── .env                      OPENAI_API_KEY, TAVILY_API_KEY, LANGFUSE_PUBLIC_KEY,
│                             LANGFUSE_SECRET_KEY, LANGFUSE_HOST (placeholders until
│                             account setup at the end)
├── .gitignore                .env, .venv/, __pycache__/, *.pyc, chroma_langchain_db/
├── requirements.txt
├── docs/hr_policies.pdf       copied from Lesson 4
├── tools/
│   ├── __init__.py
│   ├── rag_tool.py            search_hr_policies (copied, unchanged)
│   └── web_search_tool.py     web_search (copied, unchanged)
├── agent.py                   build_agent() — same logic as Lesson 4's main.py, extracted
├── observability.py           get_langfuse_handler() -> CallbackHandler | None
├── guardrails_config/
│   ├── config.yml             models, rails.input/output.flows = [self check input/output]
│   └── prompts.yml            self-check input/output policy prompts (the input/output
│                               contracts, in plain language)
├── guardrails.py               check_input(query) -> (allowed, reason)
│                                check_output(text) -> (allowed, reason)
├── main.py                    CLI loop wiring guardrails + agent + langfuse together
├── eval/
│   ├── __init__.py
│   ├── dataset.py              ~10 labeled queries + expected tool trajectories/category
│   └── run_eval.py             runs dataset through the pipeline, scores with agentevals,
│                                writes eval/results.json
├── EVALUATION.md               Part 3 deliverable: metrics + narrative, generated from
│                                eval/results.json
└── README.md                   setup + run instructions for all three parts
```

## Part 1 — LangFuse Observability

- `observability.py`: builds a `langfuse.langchain.CallbackHandler` from env vars
  (`LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_HOST`, default host
  `https://cloud.langfuse.com`). If keys are missing, `get_langfuse_handler()` returns
  `None` and callers skip passing callbacks (agent still runs, just untraced) —
  this lets the rest of the system be built and tested before the LangFuse
  account exists.
- Passed as `config={"callbacks": [handler]}` into `agent.invoke(...)`. The
  handler auto-captures, per LangChain/LangGraph callback events:
  - Token usage (input/output) from each LLM generation's usage metadata.
  - Full prompts (system + human + intermediate AI/tool messages).
  - Tool calls: name, input, output for `search_hr_policies` / `web_search`.
  - The full intermediate step tree (nested trace in the LangFuse UI).
- No manual span creation needed — this is the callback handler's job.

## Part 2 — NeMo Guardrails

- **Input contract**: reject prompt injection/jailbreak attempts, off-topic
  requests unrelated to HR policy or general research assistance, and requests
  probing for other employees' private data.
- **Output contract**: reject responses containing PII-like patterns, toxic/unsafe
  language, or fabricated legal/compliance claims not grounded in retrieved docs.
- Implemented via NeMo Guardrails' built-in self-check-input / self-check-output
  rails (LLM-as-judge against the plain-language policies above), using
  `gpt-4o-mini` for these auxiliary checks to keep them cheap and fast, separate
  from the main `gpt-4o` agent.
- `guardrails.py` loads `RailsConfig.from_path("guardrails_config")` once into an
  `LLMRails` instance, and exposes:
  - `check_input(query: str) -> tuple[bool, str]` — runs only the input rail via
    `GenerationOptions(rails=["input"])`.
  - `check_output(text: str) -> tuple[bool, str]` — runs only the output rail via
    `GenerationOptions(rails=["output"])`.
- We do **not** reimplement the ReAct tool-calling loop in Colang — guardrails sit
  as a checkpoint before and after the existing LangChain agent, not a
  replacement generation path.
- If a guardrail library call itself errors (e.g. transient API issue), it
  fails **closed** for output (better to withhold an answer than leak one) and
  **open** for input on the specific case of a transport/network error only
  (logged loudly) — actual policy violations always block.

## Part 3 — AgentEval (`agentevals`)

- `eval/dataset.py`: ~10 queries labeled into 4 categories:
  1. HR-only (expect `search_hr_policies` only)
  2. Web-only (expect `web_search` only)
  3. Mixed (expect both tools)
  4. Adversarial (expect the guardrail to block before the agent runs at all)
- `eval/run_eval.py`:
  - Runs every query through the full pipeline (guardrail-in -> agent -> guardrail-out),
    with the LangFuse handler attached.
  - Categories 1-3: score actual vs. expected tool trajectory with
    `agentevals.trajectory.create_trajectory_match_evaluator(trajectory_match_mode="unordered")`,
    plus `create_trajectory_llm_as_judge` for a qualitative reasonableness score.
  - Category 4: assert the guardrail blocked the query (agent never invoked);
    this is a direct assertion, not an agentevals call.
  - Writes per-query and aggregate results to `eval/results.json`.
- `EVALUATION.md`: hand-authored markdown template with a results table populated
  from `eval/results.json`, covering:
  - Trajectory match rate (%)
  - Tool-call precision (unnecessary calls observed)
  - LLM-judge reasonableness score (avg)
  - Guardrail block rate on adversarial inputs (target 100%)
  - Token usage per query and latency (cross-referenced from LangFuse traces)

## Config & env

- `.env`: `OPENAI_API_KEY`, `TAVILY_API_KEY` (reused from Lesson 4), plus new
  `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_HOST` placeholders —
  filled in during the guided LangFuse account setup at the end of this work.
- `requirements.txt` additions over Lesson 4's: `langfuse`, `nemoguardrails`, `agentevals`.

## Error handling

- Missing LangFuse keys -> tracing silently disabled (console warning), agent
  still works.
- Missing/invalid guardrails config -> fail loudly at startup (this is a safety
  feature, not optional).
- Empty Chroma collection -> existing Lesson 4 ingestion-on-first-run behavior,
  unchanged.
- Eval script: a single query erroring doesn't abort the whole run — caught,
  recorded as a failure for that row, run continues.

## Testing / verification

- Manual run of `main.py` with a normal HR query, a web query, and one
  jailbreak-style adversarial query — confirm guardrail blocks the last one
  and the first two produce grounded answers.
- Run `eval/run_eval.py` end-to-end, confirm `eval/results.json` and
  `EVALUATION.md` numbers are consistent.
- After LangFuse account setup, confirm a trace appears in the LangFuse UI
  showing prompts, tool calls, and token usage for a sample run.

## Out of scope (YAGNI)

- Google Docs tool (dropped per user decision — needs interactive OAuth).
- Self-hosted LangFuse (using LangFuse Cloud).
- Custom Colang conversation flows beyond self-check input/output rails.
- CI integration for the eval suite (run manually for this assignment).
- Multi-turn conversation memory (out of scope, unchanged from Lesson 4).
