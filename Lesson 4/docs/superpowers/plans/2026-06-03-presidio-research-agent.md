# Presidio Internal Research Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a LangChain ReAct agent for Presidio with three tools — RAG over HR policies, Google Docs search, and Tavily web search.

**Architecture:** `create_react_agent` wires three `@tool` functions to a `gpt-4o` LLM. The agent reasons step-by-step, selects the appropriate tool(s), and synthesizes a final answer. Each tool is isolated in its own file under `tools/`.

**Tech Stack:** LangChain, LangChain-OpenAI, LangChain-Community, LangChain-Chroma, ChromaDB, PyPDF, google-api-python-client, google-auth-oauthlib, Tavily, python-dotenv

---

## File Map

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `requirements.txt` | All project dependencies |
| Modify | `.env` | Add TAVILY_API_KEY, GOOGLE_CREDENTIALS_PATH |
| Create | `tests/__init__.py` | Make tests a package |
| Create | `tests/test_rag_tool.py` | Unit tests for RAG tool |
| Create | `tools/rag_tool.py` | RAG over hr_policies.pdf via ChromaDB |
| Create | `tests/test_web_search_tool.py` | Unit tests for web search tool |
| Modify | `tools/web_search_tool.py` | Replace stub with Tavily integration |
| Create | `tests/test_google_docs_tool.py` | Unit tests for Google Docs tool |
| Create | `tools/google_docs_tool.py` | Google Docs API via OAuth |
| Create | `tests/test_main.py` | Unit test for agent construction |
| Modify | `main.py` | Wire all tools into ReAct agent with interactive loop |

---

## Task 1: Set Up Dependencies and Environment

**Files:**
- Create: `requirements.txt`
- Modify: `.env`

- [ ] **Step 1: Create requirements.txt**

Create `requirements.txt` at the project root (`Lesson 4/requirements.txt`) with this exact content:

```
langchain>=0.3.0
langchain-openai>=0.2.0
langchain-community>=0.3.0
langchain-chroma>=0.1.4
tavily-python>=0.3.0
pypdf>=4.0.0
google-api-python-client>=2.0.0
google-auth-oauthlib>=1.0.0
python-dotenv>=1.0.0
chromadb>=0.5.0
```

- [ ] **Step 2: Install dependencies**

Run from the `Lesson 4/` directory (activate your venv first if using one):

```bash
pip install -r requirements.txt
```

Expected: all packages install without error.

- [ ] **Step 3: Add new env vars to .env**

Append these two lines to `.env` (keep the existing `OPENAI_API_KEY`):

```
TAVILY_API_KEY=<your_tavily_api_key_from_app.tavily.com>
GOOGLE_CREDENTIALS_PATH=./credentials.json
```

Replace `<your_tavily_api_key_from_app.tavily.com>` with your actual key from https://app.tavily.com.

- [ ] **Step 4: Place Google credentials file**

Copy your `credentials.json` (downloaded from Google Cloud Console → APIs & Services → Credentials) into `Lesson 4/credentials.json`.

- [ ] **Step 5: Commit**

```bash
git add requirements.txt .env
git commit -m "feat: add dependencies and env config for research agent"
```

---

## Task 2: RAG Tool (TDD)

**Files:**
- Create: `tests/__init__.py`
- Create: `tests/test_rag_tool.py`
- Create: `tools/rag_tool.py`

- [ ] **Step 1: Create test package init**

Create `tests/__init__.py` as an empty file.

- [ ] **Step 2: Write failing tests**

Create `tests/test_rag_tool.py`:

```python
from unittest.mock import patch, MagicMock
from tools.rag_tool import search_hr_policies


def test_search_returns_formatted_chunks():
    mock_doc = MagicMock()
    mock_doc.page_content = "All employees are entitled to 15 days of annual leave."
    mock_doc.metadata = {"page": 1}

    with patch("tools.rag_tool._get_vector_store") as mock_vs_fn:
        mock_vs = MagicMock()
        mock_vs._collection.count.return_value = 5
        mock_vs.similarity_search.return_value = [mock_doc]
        mock_vs_fn.return_value = mock_vs

        result = search_hr_policies.invoke("annual leave policy")

    assert "annual leave" in result
    assert "Page 1" in result


def test_empty_collection_triggers_ingest():
    mock_doc = MagicMock()
    mock_doc.page_content = "Remote work policy applies to all staff."
    mock_doc.metadata = {"page": 2}

    with patch("tools.rag_tool._get_vector_store") as mock_vs_fn, \
         patch("tools.rag_tool.PyPDFLoader") as mock_loader, \
         patch("tools.rag_tool.RecursiveCharacterTextSplitter") as mock_splitter:

        mock_vs = MagicMock()
        mock_vs._collection.count.return_value = 0
        mock_vs.similarity_search.return_value = [mock_doc]
        mock_vs_fn.return_value = mock_vs
        mock_loader.return_value.load.return_value = [mock_doc]
        mock_splitter.return_value.split_documents.return_value = [mock_doc]

        result = search_hr_policies.invoke("remote work")

    mock_vs.add_documents.assert_called_once()
    assert "Remote work policy" in result


def test_no_results_returns_fallback_message():
    with patch("tools.rag_tool._get_vector_store") as mock_vs_fn:
        mock_vs = MagicMock()
        mock_vs._collection.count.return_value = 5
        mock_vs.similarity_search.return_value = []
        mock_vs_fn.return_value = mock_vs

        result = search_hr_policies.invoke("something totally unrelated")

    assert "No relevant HR policy documents found." in result
```

- [ ] **Step 3: Run tests to verify they fail**

```bash
pytest tests/test_rag_tool.py -v
```

Expected: `ModuleNotFoundError: No module named 'tools.rag_tool'`

- [ ] **Step 4: Implement rag_tool.py**

Create `tools/rag_tool.py`:

```python
import os
from langchain.tools import tool
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

PERSIST_DIR = "./chroma_langchain_db"
COLLECTION_NAME = "presidio_collection"
PDF_PATH = "./docs/hr_policies.pdf"


def _get_vector_store() -> Chroma:
    embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=PERSIST_DIR,
    )


def _ingest_if_empty(vector_store: Chroma) -> None:
    if vector_store._collection.count() == 0:
        loader = PyPDFLoader(PDF_PATH)
        docs = loader.load()
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = splitter.split_documents(docs)
        vector_store.add_documents(chunks)


@tool("search_hr_policies")
def search_hr_policies(query: str) -> str:
    """Search Presidio's HR policy documents for policies, compliance rules, hiring guidelines, and internal procedures."""
    vector_store = _get_vector_store()
    _ingest_if_empty(vector_store)
    results = vector_store.similarity_search(query, k=3)
    if not results:
        return "No relevant HR policy documents found."
    return "\n\n---\n\n".join(
        f"[Page {doc.metadata.get('page', '?')}]: {doc.page_content}"
        for doc in results
    )
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/test_rag_tool.py -v
```

Expected: all 3 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add tests/__init__.py tests/test_rag_tool.py tools/rag_tool.py
git commit -m "feat: add RAG tool for HR policy search"
```

---

## Task 3: Web Search Tool (TDD)

**Files:**
- Create: `tests/test_web_search_tool.py`
- Modify: `tools/web_search_tool.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_web_search_tool.py`:

```python
from unittest.mock import patch
from tools.web_search_tool import web_search


def test_web_search_formats_results():
    mock_results = [
        {"url": "https://example.com/a", "content": "AI compliance regulations 2025 overview."},
        {"url": "https://example.com/b", "content": "Hiring trends in tech sector Q1 2025."},
    ]

    with patch("tools.web_search_tool._tavily") as mock_tavily:
        mock_tavily.invoke.return_value = mock_results
        result = web_search.invoke("AI compliance 2025")

    assert "https://example.com/a" in result
    assert "AI compliance regulations 2025" in result
    assert "---" in result


def test_web_search_empty_results():
    with patch("tools.web_search_tool._tavily") as mock_tavily:
        mock_tavily.invoke.return_value = []
        result = web_search.invoke("obscure query with no results")

    assert "No web search results found." in result


def test_web_search_handles_api_error():
    with patch("tools.web_search_tool._tavily") as mock_tavily:
        mock_tavily.invoke.side_effect = Exception("API rate limit exceeded")
        result = web_search.invoke("some query")

    assert "Web search error" in result
    assert "API rate limit exceeded" in result
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_web_search_tool.py -v
```

Expected: tests fail because `_tavily` does not exist on the current stub.

- [ ] **Step 3: Replace the stub with Tavily implementation**

Overwrite `tools/web_search_tool.py` entirely:

```python
from langchain.tools import tool
from langchain_community.tools.tavily_search import TavilySearchResults

_tavily = TavilySearchResults(max_results=3)


@tool("web_search")
def web_search(query: str) -> str:
    """Search the web for current information: industry benchmarks, regulatory updates, market trends, and anything not in internal documents."""
    try:
        results = _tavily.invoke(query)
        if not results:
            return "No web search results found."
        return "\n\n---\n\n".join(
            f"Source: {r.get('url', 'N/A')}\n{r.get('content', '')}"
            for r in results
        )
    except Exception as e:
        return f"Web search error: {str(e)}"
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_web_search_tool.py -v
```

Expected: all 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/test_web_search_tool.py tools/web_search_tool.py
git commit -m "feat: implement web search tool using Tavily"
```

---

## Task 4: Google Docs Tool (TDD)

**Files:**
- Create: `tests/test_google_docs_tool.py`
- Create: `tools/google_docs_tool.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_google_docs_tool.py`:

```python
from unittest.mock import patch, MagicMock
from tools.google_docs_tool import search_google_docs


def _make_services(drive_response, doc_response):
    mock_drive = MagicMock()
    mock_docs = MagicMock()
    mock_drive.files.return_value.list.return_value.execute.return_value = drive_response
    mock_docs.documents.return_value.get.return_value.execute.return_value = doc_response

    def side_effect(name, version):
        return mock_drive if name == "drive" else mock_docs

    return side_effect


def test_returns_document_content():
    drive_resp = {"files": [{"id": "doc123", "name": "Q1 Marketing Report"}]}
    doc_resp = {
        "body": {
            "content": [
                {
                    "paragraph": {
                        "elements": [{"textRun": {"content": "Campaign results were excellent."}}]
                    }
                }
            ]
        }
    }

    with patch("tools.google_docs_tool._get_google_service", side_effect=_make_services(drive_resp, doc_resp)):
        result = search_google_docs.invoke("Q1 marketing")

    assert "Q1 Marketing Report" in result
    assert "Campaign results were excellent." in result


def test_no_documents_found():
    def side_effect(name, version):
        mock_drive = MagicMock()
        mock_drive.files.return_value.list.return_value.execute.return_value = {"files": []}
        return mock_drive

    with patch("tools.google_docs_tool._get_google_service", side_effect=side_effect):
        result = search_google_docs.invoke("nonexistent topic xyz")

    assert "No Google Docs found" in result


def test_handles_api_error():
    with patch("tools.google_docs_tool._get_google_service", side_effect=Exception("OAuth token expired")):
        result = search_google_docs.invoke("any query")

    assert "Google Docs API error" in result
    assert "OAuth token expired" in result
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_google_docs_tool.py -v
```

Expected: `ModuleNotFoundError: No module named 'tools.google_docs_tool'`

- [ ] **Step 3: Implement google_docs_tool.py**

Create `tools/google_docs_tool.py`:

```python
import os
import pickle
from langchain.tools import tool
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/documents.readonly",
]
TOKEN_PATH = "./token.pickle"


def _get_google_service(service_name: str, version: str):
    creds = None
    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, "rb") as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            credentials_path = os.getenv("GOOGLE_CREDENTIALS_PATH", "./credentials.json")
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, "wb") as token:
            pickle.dump(creds, token)
    return build(service_name, version, credentials=creds)


@tool("search_google_docs")
def search_google_docs(query: str) -> str:
    """Search Presidio's Google Drive for internal documents: campaign reports, meeting notes, feedback, and company data."""
    try:
        drive_service = _get_google_service("drive", "v3")
        docs_service = _get_google_service("docs", "v1")

        response = drive_service.files().list(
            q=f"fullText contains '{query}' and mimeType='application/vnd.google-apps.document'",
            pageSize=5,
            fields="files(id, name)",
        ).execute()

        files = response.get("files", [])
        if not files:
            return f"No Google Docs found matching '{query}'."

        doc = docs_service.documents().get(documentId=files[0]["id"]).execute()
        content = ""
        for element in doc.get("body", {}).get("content", []):
            if "paragraph" in element:
                for run in element["paragraph"].get("elements", []):
                    if "textRun" in run:
                        content += run["textRun"].get("content", "")

        return f"Document: {files[0]['name']}\n\n{content.strip()[:3000]}"
    except Exception as e:
        return f"Google Docs API error: {str(e)}"
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_google_docs_tool.py -v
```

Expected: all 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add tests/test_google_docs_tool.py tools/google_docs_tool.py
git commit -m "feat: add Google Docs search tool with OAuth"
```

---

## Task 5: Wire Up ReAct Agent in main.py (TDD)

**Files:**
- Create: `tests/test_main.py`
- Modify: `main.py`

- [ ] **Step 1: Write failing test**

Create `tests/test_main.py`:

```python
from unittest.mock import patch, MagicMock


def test_build_agent_creates_executor_with_three_tools():
    with patch("main.ChatOpenAI"), \
         patch("main.create_react_agent"), \
         patch("main.AgentExecutor") as mock_executor_cls, \
         patch("main.PromptTemplate"), \
         patch("main.search_hr_policies") as mock_rag, \
         patch("main.search_google_docs") as mock_gdocs, \
         patch("main.web_search") as mock_ws:
        from main import build_agent
        build_agent()

    call_kwargs = mock_executor_cls.call_args.kwargs
    assert len(call_kwargs["tools"]) == 3
    assert mock_executor_cls.call_args.kwargs["verbose"] is True
    assert mock_executor_cls.call_args.kwargs["handle_parsing_errors"] is True
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_main.py -v
```

Expected: `ImportError` — `build_agent` does not exist yet.

- [ ] **Step 3: Rewrite main.py**

Replace the entire contents of `main.py`:

```python
from dotenv import load_dotenv
load_dotenv()

from langchain_openai import ChatOpenAI
from langchain.agents import create_react_agent, AgentExecutor
from langchain.prompts import PromptTemplate
from tools.rag_tool import search_hr_policies
from tools.google_docs_tool import search_google_docs
from tools.web_search_tool import web_search

_PROMPT_TEMPLATE = """You are Presidio's Internal Research Agent. You have access to three tools:

1. search_hr_policies: Search internal HR policy documents. Use for policies, compliance rules, hiring guidelines, and internal procedures.
2. search_google_docs: Search Presidio's Google Drive. Use for campaign data, reports, meeting notes, and company-specific internal documents.
3. web_search: Search the web. Use for industry benchmarks, regulatory updates, market trends, and external data.

Always reason about which tool(s) to use before acting. Use multiple tools when the query needs both internal and external data.

{tools}

Use the following format:
Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought:{agent_scratchpad}"""


def build_agent() -> AgentExecutor:
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    tools = [search_hr_policies, search_google_docs, web_search]
    prompt = PromptTemplate.from_template(_PROMPT_TEMPLATE)
    agent = create_react_agent(llm=llm, tools=tools, prompt=prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)


def main():
    executor = build_agent()
    print("Presidio Internal Research Agent ready. Type 'quit' to exit.\n")
    while True:
        query = input("Query: ").strip()
        if query.lower() in ("quit", "exit", "q"):
            break
        if not query:
            continue
        result = executor.invoke({"input": query})
        print(f"\nAnswer: {result['output']}\n")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_main.py -v
```

Expected: 1 test PASS.

- [ ] **Step 5: Run all tests together**

```bash
pytest tests/ -v
```

Expected: all 10 tests PASS.

- [ ] **Step 6: Commit**

```bash
git add tests/test_main.py main.py
git commit -m "feat: wire up ReAct agent with all three tools"
```

---

## Task 6: Manual Smoke Test

**Files:** none (runtime validation only)

- [ ] **Step 1: Run the agent**

```bash
python main.py
```

Expected: `Presidio Internal Research Agent ready. Type 'quit' to exit.`

Note: On first run, Google OAuth will open a browser window asking you to log in — complete the flow. A `token.pickle` file will be created for future runs.

- [ ] **Step 2: Test Query 1 — Google Docs + Web Search**

Type at the prompt:

```
Summarize all customer feedback related to our Q1 marketing campaigns.
```

Expected behavior: agent uses `search_google_docs` for internal campaign docs and `web_search` for supplementary context. Final answer synthesizes both.

- [ ] **Step 3: Test Query 2 — RAG + Web Search**

```
Compare our current hiring trend with industry benchmarks.
```

Expected behavior: agent uses `search_hr_policies` for internal hiring data, then `web_search` for industry benchmarks. Final answer compares both.

- [ ] **Step 4: Test Query 3 — RAG + Web Search**

```
Find relevant compliance policies related to AI data handling.
```

Expected behavior: agent uses `search_hr_policies` for internal compliance docs and `web_search` for regulatory context. Final answer cites both sources.

- [ ] **Step 5: Add token.pickle to .gitignore and commit**

```bash
echo "token.pickle" >> .gitignore
echo "credentials.json" >> .gitignore
echo "chroma_langchain_db/" >> .gitignore
git add .gitignore
git commit -m "chore: ignore Google auth token, credentials, and vector store"
```
