import os
from src.loader import load_and_chunk, load_document, list_documents
from src.context import contextualize_chunks
from src.embeddings import generate_embeddings
from src.store import store_chunks, get_collection
from src.retrieval import retrieve
from src.generation import generate_response

def index_documents(data_dir: str = "data") -> None:
    """Carga, trocea, contextualiza, vectoriza y guarda todos los documentos de data_dir en Chroma"""
    collection = get_collection()

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

        contextualized_chunks = contextualize_chunks(doc_content, chunks)
        embeddings = generate_embeddings(contextualized_chunks)

        store_chunks(chunks, embeddings, doc_id)

    print("Indexado completo")


def ask(query: str) -> str:
    """Pipeline completo: pregunta -> recuperación -> respuesta"""
    chunks = retrieve(query=query, n_results=5)
    response = generate_response(query, chunks)
    return response

if __name__ == "__main__":
    print("\n=== Asistente de operaciones retail ===\n")
    index_documents("data")
    while True:
        query = input("Preguta o 'salir':").strip()
        if(query.lower() == 'salir'):
            break
        if not query:
            continue

        print("\n Respuesta")
        print(ask(query))
        print()