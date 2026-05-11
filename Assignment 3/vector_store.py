import chromadb
import ollama

EMBED_MODEL = "nomic-embed-text"
COLLECTION_NAME = "rag_docs"

chroma = chromadb.Client()
collection = chroma.get_or_create_collection(COLLECTION_NAME)


def embed(texts: list[str]) -> list[list[float]]:
    return [
        ollama.embeddings(model=EMBED_MODEL, prompt=t).embedding
        for t in texts
    ]


def upsert_chunks(chunks: list[str], source: str):
    embeddings = embed(chunks)
    ids = [f"{source}_{i}" for i in range(len(chunks))]
    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=chunks,
        metadatas=[{"source": source, "chunk": i} for i in range(len(chunks))],
    )


def search(query: str, top_k: int = 5) -> list[str]:
    query_embedding = embed([query])[0]
    results = collection.query(query_embeddings=[query_embedding], n_results=top_k)
    return results["documents"][0]
