import anthropic
import os
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def generate_response(query: str, context_chunks: list[str]) -> str:
    """
    Dada una pregunta y los chunks relevantes recuperados, 
    construye el prompt y llama a Claude para generar la respuesta
    """

    context = "\n\n---\n\n".join(context_chunks)
    prompt = f"""Eres un asistente experto en operaciones retail e inventario.
    Responde la pregunta del usuario basándote ÚNICAMENTE en el contexto proporcionado.
    Si la respuesta no está en el contexto, dilo explícitamente — no inventes información.

    CONTEXTO:
    {context}

    PREGUNTA:
    {query}"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return message.content[0].text

