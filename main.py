import os
from src.loader import load_and_chunk, load_document, list_documents
from src.context import contextualize_chunks
from src.embeddings import generate_embeddings
from src.store import get_collection
from src.retrieval import retrieve
from src.generation import generate_response
from src.vector_store import store_chunks


def index_documents(data_dir: str = "data") -> None:
    """Indexa con contexto (variant='contextual'), en el backend activo."""
    from src.vector_store import BACKEND
    print(f"Backend activo: {BACKEND}")

    paths = list_documents(data_dir)
    print(f"Indexando {len(paths)} documento(s)...")

    for path in paths:
        doc_id = os.path.splitext(os.path.basename(path))[0]
        print(f"-> {doc_id}")

        doc_content = load_document(path)
        chunks = load_and_chunk(path)

        contextualized_chunks, contexts = contextualize_chunks(doc_content, chunks)
        embeddings = generate_embeddings(contextualized_chunks)
        store_chunks(chunks, embeddings, doc_id, variant="contextual", contexts=contexts)

    print("Indexado completo")


def ask(query: str) -> str:
    resultados = retrieve(query, variant="baseline")
    chunks_texto = [texto for _id, texto in resultados]
    respuesta = generate_response(query, chunks_texto)
    if not respuesta.has_sufficient_context:
        return f"{respuesta.answer}\n\n(Información no disponible: {respuesta.missing_info})"
    return respuesta.answer


def index_baseline(data_dir: str = "data") -> None:
    """Indexa sin contexto (variant='baseline'), en el backend activo."""
    for path in list_documents(data_dir):
        doc_id = os.path.splitext(os.path.basename(path))[0]
        print(f"-> {doc_id} (baseline, sin contexto)")
        chunks = load_and_chunk(path)
        embeddings = generate_embeddings(chunks)
        store_chunks(chunks, embeddings, doc_id, variant="baseline")

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