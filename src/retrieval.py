import voyageai
import os
from dotenv import load_dotenv
from src.vector_store import query_collection

load_dotenv()

client = voyageai.Client(api_key=os.getenv("VOYAGE_API_KEY"))


def retrieve(
    query: str,
    n_results: int = 5,
    variant: str = "retail_docs_baseline"
) -> list[tuple[str, str]]:
    """
    Vectoriza la pregunta y recupera los chunks más relevantes de la
    colección indicada. Devuelve (id, texto) por cada chunk recuperado.
    """
    result = client.embed(
        texts=[query],
        model="voyage-3-lite",
        input_type="query"
    )
    query_embedding = result.embeddings[0]
    return query_collection(query_embedding, n_results, variant)