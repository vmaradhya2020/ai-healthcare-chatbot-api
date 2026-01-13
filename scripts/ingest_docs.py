import argparse
import os
import sys
from pathlib import Path

# Add the parent directory to sys.path to import app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.rag import chunk_text, upsert_texts

try:
    import pypdf
except Exception:
    pypdf = None


def read_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def read_pdf_file(path: Path) -> str:
    if pypdf is None:
        raise RuntimeError("pypdf is not installed. Add pypdf to requirements or use text/markdown files.")
    reader = pypdf.PdfReader(str(path))
    texts = []
    for page in reader.pages:
        try:
            texts.append(page.extract_text() or "")
        except Exception:
            texts.append("")
    return "\n".join(texts)


def ingest(path: str, collection: str, chunk_size: int = 800, chunk_overlap: int = 150):
    p = Path(path)
    if not p.exists():
        raise SystemExit(f"Path not found: {path}")

    files = [
        f for f in p.rglob("*")
        if f.is_file() and f.suffix.lower() in {".txt", ".md", ".pdf"}
    ]
    if not files:
        print("No docs found to ingest.")
        return

    for f in files:
        if f.suffix.lower() in {".txt", ".md"}:
            text = read_text_file(f)
        elif f.suffix.lower() == ".pdf":
            text = read_pdf_file(f)
        else:
            continue
        chunks = chunk_text(text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        metadatas = [{"source": str(f), "chunk": i} for i, _ in enumerate(chunks)]
        upsert_texts(chunks, metadatas=metadatas, collection=collection)
        print(f"Ingested {len(chunks)} chunks from {f}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", default="./docs", help="Folder containing documents")
    ap.add_argument("--collection", default="specs", help="Chroma collection name")
    ap.add_argument("--chunk_size", type=int, default=800)
    ap.add_argument("--chunk_overlap", type=int, default=150)
    args = ap.parse_args()
    ingest(args.path, args.collection, chunk_size=args.chunk_size, chunk_overlap=args.chunk_overlap)
