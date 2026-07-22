from src.loader import load_and_chunk, load_document
from src.embeddings import generate_embeddings
from src.store import store_chunks, get_collection
from src.retrieval import retrieve
from src.generation import generate_response
from src.context import contextualize_chunks

def index_documents(path: str) -> None:
    """Carga, trocea, contextualiza, vectoriza y guarda los documentos en Chroma"""
    collection = get_collection()

    if collection.count() > 0:
        print("Documentos indexados, saltando paso")
        return
    
    print("Indexando documentos...")
    doc_content = load_document(path)
    chunks = load_and_chunk(path)

    print("Generando contexto por chunk...")
    contextualized_chunks = contextualize_chunks(doc_content, chunks)
    embeddings = generate_embeddings(contextualized_chunks)

    store_chunks(chunks, embeddings)
    print("Indexado completo")


def ask(query: str) -> str:
    """Pipeline completo: pregunta -> recuperación -> respuesta"""
    chunks = retrieve(query)
    response = generate_response(query, chunks)
    return response

if __name__ == "__main__":
    print("\n=== Asistente de operaciones retail ===\n")
    index_documents("data/procesos-inventario.md")
    while True:
        query = input("Preguta o 'salir':").strip()
        if(query.lower() == 'salir'):
            break
        if not query:
            continue

        print("\n Respuesta")
        print(ask(query))
        print()