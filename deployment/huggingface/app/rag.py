import os
import uuid
from typing import List, Dict, Optional, Iterable

from dotenv import load_dotenv

load_dotenv()

# ChromaDB
try:
    from chromadb import PersistentClient
    from chromadb.utils import embedding_functions
except Exception as e:
    PersistentClient = None  # type: ignore
    embedding_functions = None  # type: ignore


CHROMA_DIR = os.getenv("CHROMA_DIR", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".chroma")))
DEFAULT_COLLECTION = os.getenv("CHROMA_COLLECTION", "specs")


class SimpleHashEmbeddingFunction:
    """
    Fallback embedding function if OpenAI or sentence transformers are not available.
    Produces deterministic low-dimensional vectors from text using a simple hash.
    Note: This is NOT semantic quality, but allows basic functionality without an API key.
    """

    def __init__(self, dim: int = 128):
        self.dim = dim

    def __call__(self, input: Iterable[str]) -> List[List[float]]:  # type: ignore
        vecs: List[List[float]] = []
        for text in input:
            v = [0.0] * self.dim
            for i, ch in enumerate(text.encode("utf-8")):
                v[i % self.dim] += (float(ch) / 255.0)
            # L2 normalize
            norm = sum(x * x for x in v) ** 0.5 or 1.0
            v = [x / norm for x in v]
            vecs.append(v)
        return vecs


def _get_embedding_function():
    """Return an embedding function for Chroma.
    Priority: OpenAI -> SimpleHashEmbeddingFunction
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if embedding_functions is None:
        return SimpleHashEmbeddingFunction()
    if api_key:
        try:
            return embedding_functions.OpenAIEmbeddingFunction(
                api_key=api_key,
                model_name=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"),
            )
        except Exception:
            pass
    return SimpleHashEmbeddingFunction()


def get_collection(name: Optional[str] = None):
    """Get or create a persistent Chroma collection."""
    if PersistentClient is None:
        raise RuntimeError("ChromaDB is not installed. Please add chromadb to requirements and install.")
    os.makedirs(CHROMA_DIR, exist_ok=True)
    client = PersistentClient(path=CHROMA_DIR)
    ef = _get_embedding_function()
    coll_name = name or DEFAULT_COLLECTION
    return client.get_or_create_collection(name=coll_name, embedding_function=ef)


def chunk_text(text: str, chunk_size: int = 800, chunk_overlap: int = 150) -> List[str]:
    chunks: List[str] = []
    i = 0
    n = len(text)
    while i < n:
        j = min(i + chunk_size, n)
        chunk = text[i:j]
        chunks.append(chunk)
        if j == n:
            break
        i = j - chunk_overlap
        if i < 0:
            i = 0
    return chunks


def upsert_texts(texts: List[str], metadatas: Optional[List[Dict]] = None, collection: Optional[str] = None):
    coll = get_collection(collection)
    ids = [str(uuid.uuid4()) for _ in texts]
    coll.upsert(ids=ids, documents=texts, metadatas=metadatas or [{} for _ in texts])


def query(query_text: str, k: int = 5, collection: Optional[str] = None) -> Dict:
    coll = get_collection(collection)
    res = coll.query(query_texts=[query_text], n_results=k)
    # Normalize
    docs = res.get("documents", [[]])[0] if res else []
    metas = res.get("metadatas", [[]])[0] if res else []
    return {"documents": docs, "metadatas": metas}
