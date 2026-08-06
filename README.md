# retail-rag-pipeline

Pipeline RAG (Retrieval-Augmented Generation) construido desde cero sobre
documentación de operaciones retail. Permite hacer preguntas en lenguaje
natural sobre procesos internos (inventario, devoluciones, garantías,
proveedores, RFID, precios) y obtener respuestas fundamentadas en los
documentos, sin alucinaciones.

## Por qué sin framework

Construido deliberadamente sin LangChain ni LlamaIndex para entender cada
pieza del pipeline de forma independiente. Cada módulo tiene una única
responsabilidad y puede sustituirse sin tocar el resto.

## Stack

- **LLM (generación de respuesta):** Claude (`claude-sonnet-4-6`) vía Anthropic API
- **LLM (contextualización de chunks):** Claude (`claude-haiku-4-5`) vía Anthropic API
- **Embeddings:** Voyage AI (`voyage-3-lite`)
- **Vector store:** Chroma (persistencia local)
- **Gestión de entorno:** uv

## Arquitectura

data/ # Documentos fuente (6 documentos de operaciones retail)
src/
loader.py # Carga, lista y trocea documentos (chunking con overlap)
context.py # Genera contexto por chunk con Claude (contextual retrieval)
embeddings.py # Genera embeddings con Voyage AI
store.py # Persiste y busca vectores en Chroma (multi-colección)
retrieval.py # Recupera chunks relevantes dada una pregunta
generation.py # Construye el prompt y llama a Claude
main.py # Punto de entrada — indexado + bucle conversacional
eval.py # Evaluación de recuperación (Pass@k, posición media)


## Flujo

**Indexado (primera ejecución):**
documento → chunks (500 chars, 100 overlap) → contexto por chunk (Claude Haiku,
con prompt caching) → chunk contextualizado → embedding (Voyage) → Chroma

**Consulta:**
pregunta → embedding (Voyage, `input_type=query`) → búsqueda coseno en Chroma
→ chunks relevantes → prompt + Claude → respuesta fundamentada

## Instalación

Requiere [uv](https://github.com/astral-sh/uv).

```bash
git clone https://github.com/adriangutierrezd/retail-rag-pipeline
cd retail-rag-pipeline
uv sync
```

Crea un `.env` en la raíz:

ANTHROPIC_API_KEY=sk-ant-...
VOYAGE_API_KEY=pa-...


> Voyage AI limita a 3 RPM/10K TPM sin método de pago añadido en el dashboard
> (aunque los tokens gratis de la serie 3 se siguen aplicando). Recomendado
> añadir tarjeta antes de indexar varios documentos seguidos.

## Uso

```bash
uv run main.py
```

En la primera ejecución indexa los documentos de `data/` automáticamente,
generando contexto por chunk y guardándolo en la colección
`retail_docs_contextual`. A partir de la segunda, usa los vectores ya
persistidos en `chroma_db/`.

Para añadir documentos propios: colócalos en `data/` y elimina la colección
correspondiente para forzar un re-indexado completo:

```bash
uv run python -c "
import chromadb
client = chromadb.PersistentClient(path='chroma_db')
client.delete_collection('retail_docs_contextual')
"
```

## Contextual retrieval

Técnica de Anthropic para mejorar la precisión de recuperación en RAG:
antes de vectorizar cada chunk, se le pide a un LLM barato (`claude-haiku-4-5`)
que genere una frase situando el chunk dentro del documento completo
(usando `cache_control` para cachear el documento y abaratar llamadas
repetidas sobre el mismo documento). Ese contexto se antepone al chunk
antes de generar el embedding; el chunk mostrado al usuario sigue siendo
el original, sin el contexto pegado.

El proyecto mantiene **dos colecciones de Chroma** en paralelo para poder
comparar el efecto de esta técnica de forma controlada:

- `retail_docs_contextual` — embeddings sobre chunk + contexto generado
- `retail_docs_baseline` — embeddings sobre el chunk original, sin contexto

## Evaluación (Pass@k)

`eval.py` mide, sobre 10 preguntas con chunk correcto conocido de antemano,
si ese chunk aparece entre los resultados recuperados (Pass@k) y en qué
posición exacta (más informativo que Pass@k con un corpus pequeño).

**Resultado (2 corridas independientes, n_results=10):**

| Métrica | Contextual | Baseline |
|---|---|---|
| Pass@1 | 50-60% | **80%** |
| Pass@3 | **100%** | 90% |
| Posición media | 1.50-1.60 | **1.50** |

**Conclusión:** en este corpus (documentos cortos de 7-10 chunks, con
headers de Markdown explícitos), contextual retrieval **no mejora** la
recuperación frente al baseline — el baseline es igual o ligeramente
mejor en Pass@1, la métrica más exigente.

**Hipótesis, verificada inspeccionando el contexto real generado
(guardado en metadata):** los headers de Markdown ya aportan contexto
posicional suficiente sin coste adicional. El contexto generado por el
LLM, aunque semánticamente correcto, introduce términos de secciones
relacionadas del mismo documento (p. ej. al describir "garantía legal"
también menciona "cambio de opinión" para contrastarlo), lo cual puede
diluir la especificidad del embedding resultante en documentos ya bien
estructurados.

**Implicación práctica:** contextual retrieval no es una mejora
universal — su valor depende de cuánto contexto estructural ya provee el
documento por sí mismo. Por esta razón, **la colección activa en
producción para este proyecto es `retail_docs_baseline`**, no la
contextual. El código y la colección contextual se mantienen en el repo
como pieza de evaluación documentada, no como código muerto.

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

**n_results:** ajustado de 2 a 5 tras detectar, mediante pruebas manuales,
que con 2 resultados el sistema recuperaba información incompleta en
preguntas que requerían combinar varias secciones del mismo documento.

**IDs de chunk por documento:** cada chunk se identifica como
`{doc_id}_chunk_{i}`, no solo `chunk_{i}`, para evitar colisiones de ID
al indexar múltiples documentos en la misma colección.

## Próximos pasos

- [x] Contextual retrieval (implementado y evaluado — ver sección Evaluación)
- [x] Evals para medir calidad de recuperación (Pass@k + posición media)
- [x] Soporte para múltiples documentos
- [x] Migración de Chroma a pgvector