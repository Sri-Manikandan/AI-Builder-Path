from langchain.tools import tool
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
import pypdf

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


def _load_pdf(path: str) -> list[Document]:
    with open(path, "rb") as f:
        reader = pypdf.PdfReader(f)
        return [
            Document(page_content=page.extract_text() or "", metadata={"page": i})
            for i, page in enumerate(reader.pages)
        ]


def _ingest_if_empty(vector_store: Chroma) -> None:
    if vector_store._collection.count() == 0:
        docs = _load_pdf(PDF_PATH)
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
