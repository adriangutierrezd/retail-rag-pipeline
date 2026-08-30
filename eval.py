from src.retrieval import retrieve

EVAL_SET = [
    ("¿Cuántos días tengo para devolver un producto si simplemente no me convence?",
     ["politica-devoluciones-garantias_chunk_0"]),
    ("¿Qué pasa si el producto que compré tiene un defecto de fábrica?",
     ["politica-devoluciones-garantias_chunk_2", "politica-devoluciones-garantias_chunk_3"]),
    ("¿Cuánto dura la garantía legal de un producto?",
     ["politica-devoluciones-garantias_chunk_4"]),
    ("¿Puedo devolver ropa interior si no me gusta?",
     ["politica-devoluciones-garantias_chunk_1", "politica-devoluciones-garantias_chunk_2"]),
    ("¿Cuánto tarda en llegar un pedido urgente de un proveedor nacional?",
     ["gestion-proveedores-pedidos_chunk_2"]),
    ("¿Qué pasa si un proveedor internacional no puede acelerar una entrega?",
     ["gestion-proveedores-pedidos_chunk_2", "gestion-proveedores-pedidos_chunk_3"]),
    ("¿Cuánto tiempo tarda atención al cliente en dar una primera respuesta?",
     ["atencion-cliente-quejas_chunk_1"]),
    ("¿Cuándo se escala una queja a un responsable?",
     ["atencion-cliente-quejas_chunk_2", "atencion-cliente-quejas_chunk_3"]),
    ("¿Cada cuánto se hace inventario cíclico con RFID?",
     ["gestion-rfid-etiquetado_chunk_2", "gestion-rfid-etiquetado_chunk_3"]),
    ("¿Qué margen de descuadre de precio se permite entre tienda y web?",
     ["politica-precios-descuentos_chunk_0"]),
]


def rank_of_expected(ids_recuperados: list[str], ids_esperados: list[str]) -> int | None:
    """Devuelve la posición (1-indexada) del primer ID esperado que aparece, o None si ninguno aparece."""
    for i, id_ in enumerate(ids_recuperados, start=1):
        if id_ in ids_esperados:
            return i
    return None


def evaluate(variant: str, n_results: int = 10) -> None:
    print(f"\n=== {variant} ===\n")
    ranks = []
    pass_at_1 = 0
    pass_at_3 = 0

    for pregunta, ids_esperados in EVAL_SET:
        resultados = retrieve(pregunta, n_results=n_results, variant=variant)
        ids_recuperados = [id_ for id_, _texto in resultados]

        rank = rank_of_expected(ids_recuperados, ids_esperados)
        ranks.append(rank if rank else n_results + 1)  # penaliza si no aparece

        if rank == 1:
            pass_at_1 += 1
        if rank and rank <= 3:
            pass_at_3 += 1

        print(f"{pregunta}")
        print(f"   posición del chunk correcto: {rank if rank else 'no encontrado en top-' + str(n_results)}")
        print()

    avg_rank = sum(ranks) / len(ranks)
    print(f"Pass@1 = {pass_at_1}/{len(EVAL_SET)} = {pass_at_1/len(EVAL_SET):.0%}")
    print(f"Pass@3 = {pass_at_3}/{len(EVAL_SET)} = {pass_at_3/len(EVAL_SET):.0%}")
    print(f"Posición media del chunk correcto: {avg_rank:.2f}")


if __name__ == "__main__":
    evaluate("retail_docs_baseline")
    evaluate("retail_docs_baseline")