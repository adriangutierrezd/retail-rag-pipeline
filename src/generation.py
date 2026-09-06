import os
from anthropic import Anthropic
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv
from src.pricing import coste_claude
from src.logging_utils import log_event

load_dotenv()

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

class RetailAnswer(BaseModel):
    has_sufficient_context: bool
    answer: str
    missing_info: Optional[str] = None


def generate_response(query: str, chunks: list[str],  request_id: str | None = None) -> RetailAnswer:
    context = "\n\n".join(chunks)
    model = "claude-sonnet-4-6"
    response = client.messages.parse(
        model=model,
        max_tokens=1024,
        messages=[{"role": "user", "content": (
            f"Contexto:\n{context}\n\nPregunta: {query}\n\n"
            "Responde únicamente con la información disponible en el contexto. "
            "Si el contexto no contiene suficiente información, indícalo."
        )}],
        output_format=RetailAnswer,
    )

    log_event("llm_call", {
        "request_id": request_id,
        "modelo": model,
        "proposito": "generate_response",
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
        "coste_usd": coste_claude(model, response.usage),
    })

    return response.parsed_output


