import os

BACKEND = os.getenv("VECTOR_BACKEND", "chroma")

def store_chunks(chunks: list[str], embeddings: list[list[float]], doc_id: str, variant: str = "baseline", contexts: list[str] | None = None) -> None:
    """
    Guarda chunks en el backend activo (VECTOR BACKEND)
    siendo variant baseline o contextual sin importar el backend
    """
    if BACKEND == "postgres":
        from src.store_pg import store_chunks as _store
        _store(chunks, embeddings, doc_id, source=variant, contexts=contexts)
    else:
        from src.store import store_chunks as _store
        _store(chunks, embeddings, doc_id, collection_name=f"retail_docs_{variant}", contexts=contexts)


def query_collection(
    query_embedding: list[float],
    n_results: int = 5,
    variant: str = "baseline"
) -> list[tuple[str, str]]:
    """
    Busca chunks similares en el backend activo (VECTOR_BACKEND).
    """
    if BACKEND == "postgres":
        from src.store_pg import query_collection as _query
        return _query(query_embedding, n_results=n_results, source=variant)
    else:
        from src.store import query_collection as _query
        return _query(query_embedding, n_results=n_results, collection_name=f"retail_docs_{variant}")
    