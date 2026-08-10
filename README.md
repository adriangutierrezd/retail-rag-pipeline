# retail-rag-pipeline

Pipeline RAG (Retrieval-Augmented Generation) construido desde cero sobre
documentación de operaciones retail. Permite hacer preguntas en lenguaje
natural sobre procesos internos (inventario, devoluciones, garantías,
proveedores, RFID, precios) y obtener respuestas fundamentadas en los
documentos, sin alucinaciones — con reconocimiento explícito de cuándo
la información no está disponible.

## Por qué sin framework

Construido deliberadamente sin LangChain ni LlamaIndex para entender cada
pieza del pipeline de forma independiente. Cada módulo tiene una única
responsabilidad y puede sustituirse sin tocar el resto.

## Stack

- **LLM (generación de respuesta):** Claude (`claude-sonnet-4-6`) vía Anthropic API, con structured outputs (Pydantic)
- **LLM (contextualización de chunks):** Claude (`claude-haiku-4-5`) vía Anthropic API
- **Embeddings:** Voyage AI (`voyage-3-lite`, 512 dimensiones)
- **Vector store:** Chroma o Postgres + pgvector, intercambiable vía variable de entorno
- **Gestión de entorno:** uv

## Arquitectura

data/ # Documentos fuente (6 documentos de operaciones retail)
docker-compose.yml # Postgres + pgvector (opcional, según backend)
src/
loader.py # Carga, lista y trocea documentos (chunking con overlap)
context.py # Genera contexto por chunk con Claude (contextual retrieval)
embeddings.py # Genera embeddings con Voyage AI
store.py # Persiste y busca vectores en Chroma
store_pg.py # Persiste y busca vectores en Postgres + pgvector
vector_store.py # Despachador: elige backend según VECTOR_BACKEND
retrieval.py # Recupera chunks relevantes dada una pregunta
generation.py # Construye el prompt y llama a Claude (structured output)
main.py # Punto de entrada — indexado + bucle conversacional
eval.py # Evaluación de recuperación (Pass@k, posición media)


## Flujo

**Indexado (primera ejecución):**
documento → chunks (500 chars, 100 overlap) → contexto por chunk (Claude Haiku,
con prompt caching) → chunk contextualizado → embedding (Voyage) → vector store

**Consulta:**
pregunta → embedding (Voyage, `input_type=query`) → búsqueda por distancia
coseno → chunks relevantes → prompt + Claude → `RetailAnswer` (respuesta
estructurada y validada)

## Instalación

Requiere [uv](https://github.com/astral-sh/uv) y, si usas el backend de
Postgres, [Docker](https://docs.docker.com/get-docker/).

```bash
git clone https://github.com/adriangutierrezd/retail-rag-pipeline
cd retail-rag-pipeline
uv sync
```

Crea un `.env` en la raíz:

ANTHROPIC_API_KEY=sk-ant-...
VOYAGE_API_KEY=pa-...
POSTGRES_URL=postgresql://retail_rag:retail_rag_dev@localhost:5432/retail_rag
VECTOR_BACKEND=chroma


`VECTOR_BACKEND` acepta `chroma` (por defecto) o `postgres`.

> Voyage AI limita a 3 RPM/10K TPM sin método de pago añadido en el dashboard
> (aunque los tokens gratis de la serie 3 se siguen aplicando). Recomendado
> añadir tarjeta antes de indexar varios documentos seguidos.

### Si usas el backend de Postgres

```bash
docker compose up -d
docker exec -it retail-rag-postgres psql -U retail_rag -d retail_rag -c "CREATE EXTENSION IF NOT EXISTS vector;"
docker exec -it retail-rag-postgres psql -U retail_rag -d retail_rag -c "
CREATE TABLE chunks (
    id TEXT PRIMARY KEY,
    doc_id TEXT NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(512),
    context TEXT,
    source TEXT NOT NULL DEFAULT 'baseline'
);
CREATE INDEX ON chunks USING hnsw (embedding vector_cosine_ops);
"
```

## Uso

```bash
# Backend Chroma (por defecto)
uv run main.py

# Backend Postgres + pgvector
VECTOR_BACKEND=postgres uv run main.py
```

En la primera ejecución indexa los documentos de `data/` en la variante
`baseline` (sin contexto), que es la colección/fuente activa en producción
para este proyecto — ver sección "Contextual retrieval" para el porqué.

## Contextual retrieval

Técnica de Anthropic para mejorar la precisión de recuperación en RAG:
antes de vectorizar cada chunk, se le pide a un LLM barato (`claude-haiku-4-5`)
que genere una frase situando el chunk dentro del documento completo
(usando `cache_control` para cachear el documento y abaratar llamadas
repetidas sobre el mismo documento). Ese contexto se antepone al chunk
antes de generar el embedding; el chunk mostrado al usuario sigue siendo
el original, sin el contexto pegado.

El proyecto mantiene **dos variantes** en paralelo para poder comparar el
efecto de esta técnica de forma controlada (dos colecciones en Chroma, o
una columna `source` en Postgres):

- `contextual` — embeddings sobre chunk + contexto generado
- `baseline` — embeddings sobre el chunk original, sin contexto

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
documento por sí mismo. Por esta razón, **la variante activa en
producción para este proyecto es `baseline`**, no la contextual. El
código y la variante contextual se mantienen en el repo como pieza de
evaluación documentada, no como código muerto.

## Structured outputs

`generate_response()` no devuelve texto libre — devuelve un `RetailAnswer`
(Pydantic), usando structured outputs nativos de la API de Anthropic
(`client.messages.parse()` con `output_format`):

```python
class RetailAnswer(BaseModel):
    has_sufficient_context: bool
    answer: str
    missing_info: Optional[str] = None
```

Esto convierte el anti-alucinación de una instrucción de prompt (difícil
de verificar programáticamente) en un campo booleano fiable: el propio
código puede comprobar `has_sufficient_context` sin tener que analizar
texto libre, lo cual abre la puerta a medir la tasa de reconocimiento
honesto de falta de información como parte de la evaluación, no solo la
calidad de la recuperación.

## Decisiones técnicas

**Chunking con overlap:** cada chunk repite los últimos 100 caracteres del
anterior para evitar que información relevante quede partida en una frontera.

**input_type document vs query:** Voyage optimiza el vector de forma diferente
según si es un documento a indexar o una pregunta a buscar. Usar el tipo
correcto en cada caso mejora la calidad de la recuperación.

**Anti-alucinación estructurado:** en vez de depender de que Claude declare
en texto libre que no tiene información suficiente, el campo
`has_sufficient_context` lo hace explícito y verificable por código.

**Similitud coseno:** tanto Chroma (`hnsw:space: cosine`) como pgvector
(`vector_cosine_ops`) están configurados para medir distancia coseno,
coherente con cómo Voyage genera los embeddings.

**n_results:** ajustado de 2 a 5 tras detectar, mediante pruebas manuales,
que con 2 resultados el sistema recuperaba información incompleta en
preguntas que requerían combinar varias secciones del mismo documento.

**IDs de chunk por documento:** cada chunk se identifica como
`{doc_id}_chunk_{i}`, no solo `chunk_{i}`, para evitar colisiones de ID
al indexar múltiples documentos en la misma colección/tabla.

**Backend de vector store intercambiable:** `vector_store.py` actúa como
capa de despacho entre Chroma y Postgres + pgvector, seleccionable vía
`VECTOR_BACKEND`, sin acoplar el resto del pipeline (loader, contexto,
embeddings, generación) a un backend concreto.

## Próximos pasos

- [x] Contextual retrieval (implementado y evaluado — ver sección Evaluación)
- [x] Evals para medir calidad de recuperación (Pass@k + posición media)
- [x] Soporte para múltiples documentos
- [x] Migración de Chroma a pgvector (backend seleccionable)
- [x] Structured outputs con Pydantic
- [ ] Extender eval.py con preguntas sin cobertura, para medir la tasa de
      reconocimiento honesto de falta de información (has_sufficient_context)
- [ ] Logging estructurado por query (coste, latencia, chunks usados) para
      observabilidad real, no solo evaluación puntual