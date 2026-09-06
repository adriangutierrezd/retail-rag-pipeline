import voyageai
import os
from dotenv import load_dotenv
from src.vector_store import query_collection
from src.pricing import coste_voyage
from src.logging_utils import log_event

load_dotenv()

client = voyageai.Client(api_key=os.getenv("VOYAGE_API_KEY"))


def retrieve(
    query: str,
    n_results: int = 5,
    variant: str = "baseline",
    request_id: str | None = None
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

    log_event("embedding_call", {
        "request_id": request_id,
        "modelo": "voyage-3-lite",
        "proposito": "retrieve",
        "total_tokens": result.total_tokens,
        "coste_usd": coste_voyage(result.total_tokens),
    })

    query_embedding = result.embeddings[0]
    return query_collection(query_embedding, n_results, variant)