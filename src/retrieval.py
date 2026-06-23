import sys
sys.path.append(".")
from src.store import query_collection

def retrieve(query: str, n_results: int = 2) -> list[list]:
    """
    Dada una pregunta en lenguaje natural: 
    1. La convierte en embeddings con Voyage
    2. Busca en Chroma los chunks más cercanos
    3. Devuelve esos chunks como contexto para el LLM
    """

    import voyageai
    import os
    from dotenv import load_dotenv
    load_dotenv()

    client = voyageai.Client(api_key=os.getenv("VOYAGE_API_KEY"))
    result = client.embed(
        texts=[query],
        model="voyage-3-lite",
        input_type="query"
    )

    query_embedding = result.embeddings[0]
    chunks = query_collection(query_embedding, n_results)

    return chunks
