import os
from src.loader import load_and_chunk, load_document, list_documents
from src.context import contextualize_chunks
from src.embeddings import generate_embeddings
from src.store import store_chunks, get_collection
from src.retrieval import retrieve
from src.generation import generate_response

def index_documents(data_dir: str = "data") -> None:
    """Carga, trocea, contextualiza, vectoriza y guarda todos los documentos de data_dir en Chroma"""
    collection = get_collection("retail_docs_contextual")

    if collection.count() > 0:
        print("Documentos indexados, saltando paso")
        return

    paths = list_documents(data_dir)
    print(f"Indexando {len(paths)} documento(s)...")

    for path in paths:
        doc_id = os.path.splitext(os.path.basename(path))[0]
        print(f"-> {doc_id}")

        doc_content = load_document(path)
        chunks = load_and_chunk(path)

        contextualized_chunks, contexts = contextualize_chunks(doc_content, chunks)
        embeddings = generate_embeddings(contextualized_chunks)
        store_chunks(chunks, embeddings, doc_id, collection_name="retail_docs_contextual", contexts=contexts)

    print("Indexado completo")

def ask(query: str) -> str:
    resultados = retrieve(query)
    chunks_texto = [texto for _id, texto in resultados]
    response = generate_response(query, chunks_texto)
    return response

def index_baseline(data_dir: str = "data") -> None:
    """Indexa los mismos documentos SIN contextualizar, para comparar."""
    collection = get_collection("retail_docs_baseline")
    if collection.count() > 0:
        print("Baseline ya indexado, saltando paso")
        return

    for path in list_documents(data_dir):
        doc_id = os.path.splitext(os.path.basename(path))[0]
        print(f"-> {doc_id} (baseline, sin contexto)")
        chunks = load_and_chunk(path)
        embeddings = generate_embeddings(chunks)  # chunks originales, sin contextualize_chunks
        store_chunks(chunks, embeddings, doc_id, collection_name="retail_docs_baseline")

    print("Indexado baseline completo")

if __name__ == "__main__":
    print("\n=== Asistente de operaciones retail ===\n")
    index_baseline("data")
    while True:
        query = input("Preguta o 'salir':").strip()
        if(query.lower() == 'salir'):
            break
        if not query:
            continue

        print("\n Respuesta")
        print(ask(query))
        print()