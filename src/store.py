import chromadb
import os

def get_collection(name: str = "retail_docs_baseline"):
    """
    Devuelve (o crea si no existe) una colección de Chroma por nombre.
    Permite tener varias colecciones conviviendo en el mismo chroma_db/
    (ej. retail_docs_contextual vs retail_docs_baseline) para comparar.
    """
    client = chromadb.PersistentClient(path="chroma_db")
    return client.get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"}
    )


def store_chunks(
    chunks: list[str],
    embeddings: list[list[float]],
    doc_id: str,
    collection_name: str = "retail_docs_baseline",
    contexts: list[str] | None = None
) -> None:
    """
    Guarda los chunks y sus embeddings en la colección indicada.
    El ID combina doc_id + posición del chunk, para evitar colisiones
    cuando se indexan varios documentos en la misma colección.
    Si se pasan contexts, se guardan como metadata (para poder auditar
    después qué contexto generó Claude para cada chunk).
    """
    collection = get_collection(collection_name)
    metadatas = [{"context": c} for c in contexts] if contexts else None
    collection.add(
        ids=[f"{doc_id}_chunk_{i}" for i in range(len(chunks))],
        documents=chunks,
        embeddings=embeddings,
        metadatas=metadatas
    )
    print(f"{len(chunks)} chunks generados en '{collection_name}' para {doc_id}")


def query_collection(
    query_embedding: list[float],
    n_results: int = 5,
    collection_name: str = "retail_docs_baseline"
) -> list[tuple[str, str]]:
    """
    Busca los n_results chunks más similares en la colección indicada.
    Devuelve una lista de tuplas (id, texto) para poder identificar
    exactamente qué chunk se recuperó, no solo su contenido.
    """
    collection = get_collection(collection_name)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results
    )
    return list(zip(results["ids"][0], results["documents"][0]))