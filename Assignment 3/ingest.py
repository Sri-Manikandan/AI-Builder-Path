import os
from chunker import chunk_text
from vector_store import upsert_chunks


def load_text(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        from pypdf import PdfReader
        reader = PdfReader(file_path)
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    elif ext == ".txt":
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    else:
        raise ValueError(f"Unsupported file type: {ext}. Use PDF or TXT.")


def ingest_file(file_path: str):
    print(f"  Loading: {os.path.basename(file_path)}")
    text = load_text(file_path)
    if not text.strip():
        raise ValueError("File appears to be empty or unreadable.")
    chunks = chunk_text(text)
    print(f"  Chunks created: {len(chunks)}")
    upsert_chunks(chunks, source=os.path.basename(file_path))
    print(f"  Stored in vector DB.")
