import voyageai
import os
from dotenv import load_dotenv
from src.pricing import coste_voyage
from src.logging_utils import log_event

load_dotenv()

client = voyageai.Client(api_key=os.getenv("VOYAGE_API_KEY"))
def generate_embeddings(chunks: list[str]) -> list[list[float]]:
    """
    Convierte una lista de chunks en una lista de vectores numéricos.
    Devuelve una lista en el mismo orden que los chunks recibidos.
    """

    result = client.embed(
        texts=chunks,
        model="voyage-3-lite",
        input_type="document"
    )

    log_event("embedding_call", {
        "modelo": "voyage-3-lite",
        "proposito": "generate_embeddings",
        "num_chunks": len(chunks),
        "total_tokens": result.total_tokens,
        "coste_usd": coste_voyage(result.total_tokens),
    })

    return result.embeddings
