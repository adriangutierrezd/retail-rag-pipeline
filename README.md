# retail-rag

Pipeline RAG (Retrieval-Augmented Generation) construido desde cero sobre
documentación de operaciones retail. Permite hacer preguntas en lenguaje
natural sobre procesos internos (inventario, devoluciones, sincronización
de stock) y obtener respuestas fundamentadas en los documentos, sin alucinaciones.

## Por qué sin framework

Construido deliberadamente sin LangChain ni LlamaIndex para entender cada
pieza del pipeline de forma independiente. Cada módulo tiene una única
responsabilidad y puede sustituirse sin tocar el resto.

## Stack

- **LLM:** Claude (claude-sonnet-4-6) vía Anthropic API
- **Embeddings:** Voyage AI (voyage-3-lite)
- **Vector store:** Chroma (persistencia local)
- **Gestión de entorno:** uv

## Arquitectura

data/                     # Documentos fuente
src/
loader.py                 # Carga y trocea documentos (chunking con overlap)
embeddings.py             # Genera embeddings con Voyage AI
store.py                  # Persiste y busca vectores en Chroma
retrieval.py              # Recupera chunks relevantes dada una pregunta
generation.py             # Construye el prompt y llama a Claude
main.py                   # Punto de entrada — indexado + bucle conversacional

## Flujo

**Indexado (primera ejecución):**
documento → chunks (500 chars, 100 overlap) → embeddings (Voyage) → Chroma

**Consulta:**
pregunta → embedding (Voyage, input_type=query) → búsqueda coseno en Chroma
→ chunks relevantes → prompt + Claude → respuesta fundamentada

## Instalación

Requiere [uv](https://github.com/astral-sh/uv).

```bash
git clone https://github.com/adriangutierrezd/retail-rag
cd retail-rag
uv sync
```

Crea un `.env` en la raíz:

ANTHROPIC_API_KEY=sk-ant-...
VOYAGE_API_KEY=pa-...

## Uso

```bash
uv run main.py
```

En la primera ejecución indexa los documentos de `data/` automáticamente.
A partir de la segunda, usa los vectores ya persistidos en `chroma_db/`.

Para añadir documentos propios: colócalos en `data/` y elimina la carpeta
`chroma_db/` para forzar un re-indexado completo.

## Decisiones técnicas

**Chunking con overlap:** cada chunk repite los últimos 100 caracteres del
anterior para evitar que información relevante quede partida en una frontera.

**input_type document vs query:** Voyage optimiza el vector de forma diferente
según si es un documento a indexar o una pregunta a buscar. Usar el tipo
correcto en cada caso mejora la calidad de la recuperación.

**Anti-alucinación:** el prompt instruye a Claude a responder únicamente con
el contexto proporcionado y a declarar explícitamente cuando la información
no está disponible.

**Similitud coseno:** Chroma está configurado con `hnsw:space: cosine` para
medir distancia entre vectores, coherente con cómo Voyage genera los embeddings.

## Próximos pasos

- [ ] Contextual retrieval (técnica de Anthropic para mejorar precisión)
- [ ] Evals para medir calidad de recuperación
- [ ] Soporte para múltiples documentos
- [ ] Migración de Chroma a pgvector