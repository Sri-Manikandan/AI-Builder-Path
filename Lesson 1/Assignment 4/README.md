# Assignment 3 — RAG Chatbot with Ollama + ChromaDB

## Overview

A fully local **Retrieval-Augmented Generation (RAG)** chatbot built from scratch — no LangChain, no LlamaIndex. Upload a PDF or TXT document, and the chatbot answers questions about it using semantic search + a locally running LLM via Ollama.

**Stack:** Ollama (`llama3.2` + `nomic-embed-text`) · ChromaDB · pypdf

---

## Architecture — 2-Stage Pipeline

### Stage 1 — Ingest & Index *(runs once on document upload)*

```
User provides PDF / TXT file
      ↓
[File Loader] — Read and extract raw text
      ↓
[Chunker] — Split into ~500 word overlapping chunks
      ↓
[Ollama Embeddings] — nomic-embed-text converts each chunk → dense vector
      ↓
[ChromaDB] — Store vectors + chunk text + metadata
      ↓
Ready to answer questions
```

### Stage 2 — Chat & Answer *(runs on each question)*

```
User asks a question
      ↓
[Ollama Embeddings] — Embed the query into a dense vector
      ↓
[ChromaDB] — Similarity search → retrieve top-5 relevant chunks
      ↓
[Context Builder] — Assemble retrieved chunks as context
      ↓
[Ollama LLM] — llama3.2 generates a grounded answer
      ↓
Display answer to user
```

---

## Prerequisites

1. **Install Ollama** — download from [ollama.com](https://ollama.com)
2. **Pull required models:**

```bash
ollama pull llama3.2
ollama pull nomic-embed-text
```

3. **Install Python dependencies:**

```bash
pip install -r requirements.txt
```

---

## How to Run

```bash
python main.py path/to/your/document.pdf
```

Or run without arguments and enter the path when prompted:

```bash
python main.py
```

**Example session:**
```
=========================================
   RAG Chatbot — Ollama + ChromaDB
=========================================

Ingesting document...
  Loading: sample.pdf
  Chunks created: 42
  Stored in vector DB.
Ready!

Ask questions about your document. Type 'exit' to quit.

You: What is the main topic of this document?
Assistant: The document focuses on...

You: exit
Goodbye!
```

---

## Project Files

| File | Purpose |
|------|---------|
| `main.py` | Entry point — wires ingest + chat together |
| `ingest.py` | Loads PDF/TXT and ingests into ChromaDB |
| `chunker.py` | Splits text into overlapping chunks |
| `vector_store.py` | Embedding + ChromaDB upsert and search |
| `chat.py` | Query handler + Ollama LLM response |
| `requirements.txt` | Python dependencies |

---

## Key Design Decisions

- **No LangChain / LlamaIndex** — built from scratch to understand every layer.
- **Fully local** — Ollama runs the LLM and embeddings on your machine; no API keys needed.
- **`nomic-embed-text`** — fast, high-quality local embedding model.
- **`llama3.2`** — compact but capable local chat model.
- **Chunk size ~500 words with 50-word overlap** — balances retrieval precision and context richness.
- **Top-k = 5** — retrieves enough context without overloading the LLM prompt.
