import anthropic
import os
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

DOCUMENT_CONTEXT_PROMPT = """
<document>
{doc_content}
</document>
"""

CHUNK_CONTEXT_PROMPT = """
Aquí está el fragmento que queremos situar dentro del documento completo
<chunk>
{chunk_content}
</chunk>

Da un contexto breve y conciso para situar este fragmento dentro del documento completo,
con el objetivo de mejorar su recuperación en una búsqueda semántica.
Responde únicamente con ese contexto, sin nada más.
"""

def situate_context(doc: str, chunk: str) -> str:
    """
    Genera una frase de contexto que sitúa un chunk dentro de su documento de origen.
    Usa cache_control sobre el documento completo: si se llama varias veces seguidas
    con el mismo `doc`, Anthropic reutiliza la caché (~90% de descuento a partir
    del segundo chunk del mismo documento).
    """
    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=200,
        temperature=0.0,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": DOCUMENT_CONTEXT_PROMPT.format(doc_content=doc),
                        "cache_control": {"type": "ephemeral"}
                    },
                    {
                        "type": "text",
                        "text": CHUNK_CONTEXT_PROMPT.format(chunk_content=chunk)
                    }
                ]
            }
        ]
    )

    return response.content[0].text

def contextualize_chunks(doc_content: str, chunks: list[str]) -> list[str]:
    """
    Genera el texto contextualizado (contexto + chunk original) para cada chunk
    de un mismo documento, en orden secuencial para aprovechar el prompt caching.
    """
    contextualized = []
    for chunk in chunks:
        context = situate_context(doc_content, chunk)
        contextualized.append(f"{context}\n\n{chunk}")
    return contextualized

