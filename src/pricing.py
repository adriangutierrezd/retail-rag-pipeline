# Precios verificados en platform.claude.com/docs (USD por millón de tokens)
PRECIOS_CLAUDE = {
    "claude-sonnet-4-6": {"input": 3.00, "output": 15.00},
    "claude-haiku-4-5": {"input": 1.00, "output": 5.00},
}
PRECIO_VOYAGE_INPUT = 0.02  # voyage-3-lite, por millón de tokens


def coste_claude(model: str, usage) -> float:
    """
    Calcula el coste en USD de una llamada a Claude, incluyendo
    prompt caching: cache_creation se cobra a 1.25x el precio normal
    de entrada, cache_read se cobra a 0.1x (90% de descuento).
    """
    if model not in PRECIOS_CLAUDE:
        raise ValueError(
            f"Modelo '{model}' no tiene precio registrado en PRECIOS_CLAUDE. "
            f"Modelos conocidos: {list(PRECIOS_CLAUDE.keys())}. "
            "Añade su tarifa antes de usarlo para no perder visibilidad de coste."
        )
        
    precio = PRECIOS_CLAUDE[model]
    coste = usage.input_tokens * \
        precio["input"] + usage.output_tokens * precio["output"]

    cache_creation = getattr(usage, "cache_creation_input_tokens", 0) or 0
    cache_read = getattr(usage, "cache_read_input_tokens", 0) or 0
    coste += cache_creation * precio["input"] * 1.25
    coste += cache_read * precio["input"] * 0.1

    return round(coste / 1_000_000, 6)


def coste_voyage(total_tokens: int) -> float:
    """Calcula el coste en USD de una llamada de embeddings a Voyage."""
    return round(total_tokens * PRECIO_VOYAGE_INPUT / 1_000_000, 6)
