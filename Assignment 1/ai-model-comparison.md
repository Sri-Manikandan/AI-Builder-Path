# Assignment 1 — AI Model Comparison Sheet

---

## Scope & Methodology

This comparison evaluates four AI models — **GPT-4o**, **Claude Sonnet**, **Gemini Flash**, and **DeepSeek-R1:7b** (local via Ollama) — across three department-relevant use cases:

- **AppDev** → Code Generation
- **Data** → SQL Generation & Data Analysis
- **DevOps** → Infrastructure Automation

Ratings are based on synthesized research from published benchmarks (SWE-bench, HumanEval, LiveCodeBench), independent evaluations, and community comparisons as of May 2026. The local model (DeepSeek-R1:7b) was assessed on a standard Apple Silicon MacBook (M1/M2, 16 GB RAM) via the Ollama REST API.

---

## Comparison Table

| Model | Code Quality | SQL Generation | Infra Automation | Ease of Use | Speed / Latency | Comments |
|-------|:------------:|:--------------:|:----------------:|:-----------:|:---------------:|---------|
| **GPT-4o** | `Excellent` | `Excellent` | `Excellent` | `Excellent` | `Good` | ~90% HumanEval. Best for boilerplate, CRUD generation, multi-file scaffolding, and schema migrations. Strong at documentation-heavy code. Slightly slower than Flash-class models. Minor inefficiencies in query optimization (sometimes sacrifices performance for correctness). |
| **Claude Sonnet** | `Excellent` | `Excellent` | `Good` | `Excellent` | `Good` | 79.6% SWE-bench Verified (2026). Top-ranked for refactoring, debugging, and algorithm-dense code. Highest SQL accuracy in independent tests — correctly handled all complex multi-table join queries. 1M token context enables large schema analysis. Infra automation solid but slightly more verbose than GPT-4o on IaC boilerplate. |
| **Gemini Flash** | `Good` | `Good` | `Good` | `Good` | `Excellent` | 78% SWE-bench (Gemini 3 Flash). Optimized for speed — sub-second responses at a fraction of the cost of Pro-class models. ~70% accuracy on SQL tests; occasional syntax errors on edge-case queries. Strong for Python infrastructure scripts and load-testing automation. 1M token context window helps with large monorepos. Best cost-to-performance ratio for high-volume tasks. |
| **DeepSeek-R1:7b** *(Ollama, local)* | `Basic` | `Basic` | `Basic` | `Basic` | `Good` | Distilled from DeepSeek-R1 (Qwen2.5 base). 37.6% LiveCodeBench — handles simple functions and reasoning tasks but struggles with multi-file projects. SQL limited to straightforward queries; no native schema reasoning, fails on complex JOINs without fine-tuning. IaC generation inconsistent (e.g., Terraform syntax errors). Requires Ollama + 8GB+ RAM; no GUI. Advantage: fully local, no API cost, 20–55 tok/s on Apple Silicon. |

---

## Department-Specific Observations

### AppDev — Code Generation
GPT-4o and Claude Sonnet are the strongest choices. GPT-4o excels at scaffolding large boilerplate-heavy applications (REST APIs, CRUD layers, Next.js pages), while Claude Sonnet produces cleaner algorithmic code with better refactoring capabilities. Gemini Flash is a viable option where speed and cost matter more than depth. DeepSeek-R1:7b can assist with isolated utility functions but is not suitable for end-to-end feature development.

### Data — SQL Generation & Analysis
Claude Sonnet leads SQL generation accuracy, correctly handling complex multi-table JOINs, CTEs, and window functions. GPT-4o is a close second, strong on business logic but occasionally produces unoptimized queries. Gemini Flash achieves ~70% accuracy — adequate for standard analytical queries but risks syntax errors on edge cases. DeepSeek-R1:7b requires explicit schema context and fine-tuning for reliable SQL output; not recommended for production data workflows without customization.

### DevOps — Infrastructure Automation
GPT-4o is the most consistent for IaC generation (Terraform, Ansible, Dockerfiles, CI/CD YAML). Claude Sonnet is strong but occasionally verbose. Gemini Flash handles infrastructure scripting and load-testing scenarios well, with fast iteration cycles. DeepSeek-R1:7b can produce basic shell scripts and simple Docker configurations but is unreliable for complex multi-resource Terraform modules.

---

## Summary Recommendation

| Use Case | Recommended Model | Runner-Up |
|----------|------------------|-----------|
| Complex code generation / refactoring | Claude Sonnet | GPT-4o |
| SQL generation & data analysis | Claude Sonnet | GPT-4o |
| Infrastructure automation & IaC | GPT-4o | Gemini Flash |
| High-volume, cost-sensitive tasks | Gemini Flash | — |
| Offline / air-gapped / no-cost usage | DeepSeek-R1:7b | — |

For most enterprise AppDev and Data workloads, **Claude Sonnet** offers the best balance of accuracy and context capacity. **GPT-4o** is the stronger default for DevOps automation. **Gemini Flash** is the go-to when throughput and cost-efficiency are the primary constraints. **DeepSeek-R1:7b** is best suited for local experimentation, privacy-sensitive contexts, or prototyping where API access is unavailable.
