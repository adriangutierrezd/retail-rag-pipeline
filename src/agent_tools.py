from typing import Literal, Optional
from pydantic import BaseModel
from src.retrieval import retrieve
from src.generation import generate_response

TipoDecision = Literal["aprobar", "rechazar", "requiere_autorizacion_humana"]

class DecisionDevolucion(BaseModel):
    decision: TipoDecision
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
        "name": "consultar_historial_cliente",
        "description": "Consulta cuántas devoluciones ha hecho un cliente recientemente, útil para detectar patrones de abuso o casos que requieran más atención.",
        "input_schema": {
            "type": "object",
            "properties": {
                "cliente_id": {
                    "type": "string",
                    "description": "Identificador del cliente, ej. 'cliente_001'"
                }
            },
            "required": ["cliente_id"]
        }
    },
    {
        "name": "enviar_decision",
        "description": "Emite la decisión final sobre la solicitud de devolución, una vez se ha consultado la política necesaria.",
        "input_schema": DecisionDevolucion.model_json_schema()
    }
]

HISTORIAL_CLIENTES = {
    "cliente_001": {"devoluciones_ultimos_30_dias": 4, "devoluciones_ultimo_anio": 9},
    "cliente_002": {"devoluciones_ultimos_30_dias": 0, "devoluciones_ultimo_anio": 1},
    "cliente_003": {"devoluciones_ultimos_30_dias": 1, "devoluciones_ultimo_anio": 3},
}

def consultar_historial_cliente(cliente_id: str) -> str:
    """
    Ejecuta la herramienta: consulta el historial de devoluciones de un cliente.
    ---> Datos simulados en memoria
    """
    historial = HISTORIAL_CLIENTES.get(cliente_id)
    if historial is None:
        return f"No hay historial registrado para el cliente {cliente_id}. Se asume cliente sin datos de devoluciones."

    return (
        f"Cliente {cliente_id}: {historial['devoluciones_ultimos_30_dias']} devoluciones "
        f"en los últimos 30 días, {historial['devoluciones_ultimo_anio']} en el último año."
    ) 
