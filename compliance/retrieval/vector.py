"""Optional ChromaDB vector index (enabled with RETRIEVAL=hybrid)."""
from __future__ import annotations

from compliance.config import get_settings
from compliance.models import Passage

COLLECTION = "passages"


def _embedding_function():
    settings = get_settings()
    from chromadb.utils import embedding_functions

    if settings.embeddings == "openai":
        import os

        return embedding_functions.OpenAIEmbeddingFunction(
            api_key=os.environ["OPENAI_API_KEY"], model_name=settings.openai_embed_model
        )
    return embedding_functions.DefaultEmbeddingFunction()


def _collection():
    import chromadb

    client = chromadb.PersistentClient(path=str(get_settings().chroma_dir))
    return client.get_or_create_collection(
        COLLECTION, embedding_function=_embedding_function(), metadata={"hnsw:space": "cosine"}
    )


def rebuild(passages: list[Passage], batch: int = 64) -> int:
    import chromadb

    client = chromadb.PersistentClient(path=str(get_settings().chroma_dir))
    try:
        client.delete_collection(COLLECTION)
    except Exception:  # collection did not exist
        pass
    col = _collection()
    for i in range(0, len(passages), batch):
        chunk = passages[i : i + batch]
        col.add(
            ids=[p.id for p in chunk],
            documents=[f"{p.heading}\n{p.text}" for p in chunk],
            metadatas=[{"jurisdiction": p.jurisdiction, "source_id": p.source_id} for p in chunk],
        )
    return col.count()


class VectorIndex:
    def __init__(self, passages: list[Passage]):
        self._by_id = {p.id: p for p in passages}
        self._col = _collection()

    def search(self, query: str, k: int = 8, jurisdictions: set[str] | None = None) -> list[tuple[Passage, float]]:
        where = None
        if jurisdictions:
            codes = sorted(jurisdictions)
            where = {"jurisdiction": codes[0]} if len(codes) == 1 else {"jurisdiction": {"$in": codes}}
        res = self._col.query(query_texts=[query], n_results=k, where=where)
        out = []
        for pid, dist in zip(res["ids"][0], res["distances"][0]):
            if pid in self._by_id:
                out.append((self._by_id[pid], 1.0 - float(dist)))
        return out
