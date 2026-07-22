import chromadb
import os

def get_collection(collection_name: str = "retail-docs") -> chromadb.Collection:
    """
    Crea o recupera una nueva colección de Chroma persistida en disco.
    Si ya existe, la devuelve tal cual - los datos no se pierden entre ejecuciones.
    """

    client = chromadb.PersistentClient(path="chroma_db")
    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}
    )

    return collection

def store_chunks(chunks: list[str], embeddings: list[list[float]], doc_id: str) -> None:
    """
    Guarda los chunks y sus embeddings en Chroma.
    El ID combina doc_id (nombre del documento de origen) + posición del chunk
    para evitar colisiones cuando se indexan varios documentos.
    """

    collection = get_collection()
    collection.add(
        ids=[f"{doc_id}_chunk_{i}" for i in range(len(chunks))],
        documents=chunks,
        embeddings=embeddings
    )
    print(f"{len(chunks)} chunks generados en Chroma para {doc_id}")

def query_collection(query_embedding: list[float], n_results: int = 2) -> list[str]:
    """
    Dada la pregunta vectorizada, devuelve los n chunks más cercanos
    """
    coll = get_collection()
    results = coll.query(
        query_embeddings=[query_embedding],
        n_results=n_results
    )

    return results["documents"][0]
