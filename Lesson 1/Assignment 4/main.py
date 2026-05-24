import sys
import os
from ingest import ingest_file
from chat import chat_loop


def main():
    print("=" * 45)
    print("   RAG Chatbot — Ollama + ChromaDB")
    print("=" * 45)

    if len(sys.argv) >= 2:
        file_path = sys.argv[1]
    else:
        file_path = input("\nEnter path to PDF or TXT file: ").strip()

    if not os.path.exists(file_path):
        print(f"Error: File not found — {file_path}")
        sys.exit(1)

    print(f"\nIngesting document...")
    ingest_file(file_path)
    print("Ready!\n")

    chat_loop()


if __name__ == "__main__":
    main()
