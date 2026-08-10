import os
from anthropic import Anthropic
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

class RetailAnswer(BaseModel):
    has_sufficient_context: bool
    answer: str
    missing_info: Optional[str] = None

def generate_response(query: str, chunks: list[str]) -> RetailAnswer:
    """
    Genera una respuesta estructurada a partir de los chunks recuperados.
    Devuelve un RetailAnswer, no un string: el propio código puede
    comprobar has_sufficient_context sin tener que analizar texto libre.
    """
    context = "\n\n".join(chunks)
    response = client.messages.parse(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": (
                f"Contexto:\n{context}\n\n"
                f"Pregunta: {query}\n\n"
                "Responde únicamente con la información disponible en el contexto. "
                "Si el contexto no contiene suficiente información para responder "
                "con seguridad, indícalo explícitamente."
            )
        }],
        output_format=RetailAnswer,
    )
    return response.parsed_output



