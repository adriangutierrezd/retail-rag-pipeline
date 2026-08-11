from typing import Literal, Optional
from pydantic import BaseModel
from src.retrieval import retrieve
from src.generation import generate_response

class DecisionDevolucion(BaseModel):
    decision: Literal["aprobar", "rechazar", "requiere_autorizacion_humana"]
    razonamiento: str
    politica_aplicada: str
    requiere_revision: bool

def consultar_politica_devoluciones(pregunta: str) -> str:
    """
    Ejecuta la herramienta: reutiliza el RAG existente (retrieve + generate_response)
    para responder sobre políticas
    """
    resultados = retrieve(pregunta, variant="baseline")
    chunks_texto = [texto for _id, texto in resultados]
    respuesta = generate_response(pregunta, chunks_texto)
    return respuesta.answer

TOOLS = [
    {
        "name": "consultar_politica_devoluciones",
        "description": "Consulta la política de devoluciones y garantías de la tienda para resolver dudas sobre plazos, condiciones o excepciones.",
        "input_schema": {
            "type": "object",
            "properties": {
                "pregunta": {
                    "type": "string",
                    "description": "Pregunta concreta a consultar en la política, ej. 'plazo de devolución por producto defectuoso'"
                }
            },
            "required": ["pregunta"]
        }
    }, 
    {
        "name": "enviar_decision",
        "description": "Emite la decisión final sobre la solicitud de devolución, una vez se ha consultado la política necesaria.",
        "input_schema": DecisionDevolucion.model_json_schema()
    }
]