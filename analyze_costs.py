import json
from collections import defaultdict


def resumen_costes() -> dict:
    """
    Calcula el coste acumulado agrupado por propósito y por modelo,
    leyendo todo el histórico de logs/events.jsonl.
    """
    costes_por_proposito = defaultdict(float)
    costes_por_modelo = defaultdict(float)
    total = 0.0

    with open("logs/events.jsonl") as f:
        for linea in f:
            evento = json.loads(linea)
            if "coste_usd" in evento:
                costes_por_proposito[evento["proposito"]] += evento["coste_usd"]
                costes_por_modelo[evento.get("modelo", "desconocido")] += evento["coste_usd"]
                total += evento["coste_usd"]

    return {
        "por_proposito": dict(costes_por_proposito),
        "por_modelo": dict(costes_por_modelo),
        "total": total,
    }


def imprimir_resumen_costes() -> None:
    """Imprime en consola el resumen calculado por resumen_costes()."""
    resumen = resumen_costes()

    print("Coste por propósito:")
    for proposito, coste in resumen["por_proposito"].items():
        print(f"  {proposito}: ${coste:.6f}")

    print("\nCoste por modelo:")
    for modelo, coste in resumen["por_modelo"].items():
        print(f"  {modelo}: ${coste:.6f}")

    print(f"\nTotal acumulado: ${resumen['total']:.6f}")


def coste_de_peticion(request_id: str) -> float:
    """Suma el coste de todos los eventos asociados a un request_id concreto."""
    total = 0.0
    with open("logs/events.jsonl") as f:
        for linea in f:
            evento = json.loads(linea)
            if evento.get("request_id") == request_id and "coste_usd" in evento:
                total += evento["coste_usd"]
    return total


if __name__ == "__main__":
    imprimir_resumen_costes()