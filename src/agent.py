import os
from anthropic import Anthropic
from dotenv import load_dotenv
from src.agent_tools import TOOLS, consultar_politica_devoluciones, consultar_historial_cliente, DecisionDevolucion

load_dotenv()

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT="""
Eres un agente que resuelve solicitudes de devolución en una tienda retail.
Tu trabajo es:
1. Consultar la política de devoluciones cuando necesites confirmar plazos o condiciones.
2. Si el caso es ambiguo o el cliente presenta un patrón inusual de devoluciones,
   consulta también su historial para tomar una decisión más informada.
3. Tomar una decisión: aprobar, rechazar, o marcar como "requiere_autorizacion_humana"
   si la política indica que el caso necesita autorización de un encargado
   (por ejemplo, reembolsos superiores a 150€, casos ambiguos, o un historial
   de devoluciones que sugiera posible abuso).
4. Emitir tu decisión final llamando a la herramienta enviar_decision, citando
   siempre la sección de política concreta en la que te basas.
No inventes información que no esté en la política o el historial consultado.
"""

def ejecutar_tool(name: str, input_data: dict) -> str:
    """Ejecuta la herramienta real correspondiente a lo que pidió Claude"""
    if name == "consultar_politica_devoluciones":
        return consultar_politica_devoluciones(input_data["pregunta"])
    if name == "consultar_historial_cliente":
        return consultar_historial_cliente(input_data["cliente_id"])
    raise ValueError(f"Herramienta desconocida {name}")


def resolver_devolucion(caso: str, importe: float, cliente_id: str) -> DecisionDevolucion:
    """
    Bucle del agente: Claude decide qué herramientas llamar, las ejecutamos,
    le devolvemos el resultado hasta que emite la decisión final.
    Aplica una verificación adicional en código sobre el umbral de 150€,
    independiente del razonamiento del agente (guardrail de seguridad).
    """
    messages = [{
        "role": "user",
        "content": f"{caso}\n\nImporte del producto: {importe}€\nCliente: {cliente_id}"
    }]
    
    while True:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages
        )
        messages.append({"role": "assistant", "content": response.content})
        tool_results = []
        decision_final = None

        for block in response.content:
            if block.type != "tool_use":
                continue

            print(f"[agente] llamando a {block.name}({block.input})")

            if block.name == "enviar_decision":
                decision_final = DecisionDevolucion(**block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": "Decisión registrada"
                })
            else:
                resultado = ejecutar_tool(block.name, block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": resultado
                })

        if decision_final:
            return aplicar_guardrail_importe(decision_final, importe)

        messages.append({"role": "user", "content": tool_results})


def aplicar_guardrail_importe(decision: DecisionDevolucion, importe: float) -> DecisionDevolucion:
    """
    Guardrail en código: si el importe supera 150€, fuerza
    requiere_autorizacion_humana, sin depender de que el agente
    lo haya aplicado correctamente por sí solo.
    """
    UMBRAL_AUTORIZACION = 150.0

    if importe > UMBRAL_AUTORIZACION and decision.decision == "aprobar":
        print(f"[guardrail] Importe {importe}€ supera el umbral de {UMBRAL_AUTORIZACION}€. Forzando revisión humana.")
        return DecisionDevolucion(
            decision="requiere_autorizacion_humana",
            razonamiento=f"{decision.razonamiento}\n\n[Guardrail de código]: el importe ({importe}€) supera el umbral de {UMBRAL_AUTORIZACION}€, se fuerza autorización humana independientemente del análisis del agente.",
            politica_aplicada=decision.politica_aplicada,
            requiere_revision=True
        )

    return decision