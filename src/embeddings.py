import voyageai
import os
from dotenv import load_dotenv

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

    return result.embeddings
