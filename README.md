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

## Agente de conciliación de devoluciones

Primera pieza de la Fase 2 del roadmap (agentes y producción): un agente
con tool use real que resuelve solicitudes de devolución de forma
autónoma, en vez de solo responder preguntas sobre política.

A diferencia del resto del pipeline (una única llamada a Claude por
pregunta), el agente ejecuta un **bucle**: Claude decide qué herramienta
necesita, el código la ejecuta de verdad, el resultado vuelve a Claude,
y así hasta que Claude tiene información suficiente para emitir una
decisión final.

**Herramientas disponibles:**

- `consultar_politica_devoluciones` — reutiliza el RAG existente
  (`retrieve` + `generate_response`) como herramienta del agente, en vez
  de construir un sistema de consulta aparte.
- `enviar_decision` — no ejecuta ninguna acción externa; es el mecanismo
  por el que el agente entrega su decisión final en formato estructurado
  y validado (`DecisionDevolucion`, Pydantic), tratando la respuesta
  final como una herramienta más dentro del mismo bucle de tool use.

```python
class DecisionDevolucion(BaseModel):
    decision: Literal["aprobar", "rechazar", "requiere_autorizacion_humana"]
    razonamiento: str
    politica_aplicada: str
    requiere_revision: bool
```

**Guardrail de negocio, en dos capas:**

1. El agente decide de forma autónoma, consultando la política real, y
   ya respeta correctamente el umbral de 150€ definido en
   `politica-devoluciones-garantias.md` por su propio razonamiento.
2. Además, el importe se pasa como parámetro explícito de la función
   (no se extrae de texto libre) y `aplicar_guardrail_importe()` verifica
   en código, de forma independiente al razonamiento del agente, que
   ninguna devolución superior a 150€ pueda quedar aprobada
   automáticamente — corrigiendo la decisión solo si el agente se
   equivocara, sin tocar decisiones ya correctas de rechazo o revisión.

Esta doble capa refleja una decisión de diseño real de LLMOps: confiar en
el razonamiento del modelo para casos generales, pero no depender
exclusivamente de él en decisiones con impacto económico directo — un
guardrail barato en código elimina un riesgo completo, sin restar
autonomía al agente en el resto de casos.

**Ejemplo de comportamiento dinámico:** ante el mismo caso base (camiseta de
30€, devuelta a los 5 días, dentro de política), el agente consulta el
historial del cliente de forma preventiva antes de decidir. Con un cliente
sin historial de abuso, aprueba directamente. Con un cliente con 4
devoluciones en 30 días, la misma consulta cambia la decisión final a
`requiere_autorizacion_humana`, aunque el caso aislado cumplía todas las
condiciones de plazo e importe. La consulta al historial no depende de
conocer el resultado de antemano — es una práctica preventiva que el agente
aplica según la instrucción del sistema; lo que cambia la decisión es cómo
interpreta el resultado una vez obtenido.

**Fiabilidad y no-determinismo:** el agente no reutiliza la misma
redacción de pregunta entre ejecuciones del mismo caso (comportamiento
esperado de un LLM sin `temperature` fijada). En una prueba con el
mismo caso repetido 5 veces, esto llevó en una ocasión a que una
redacción distinta ("devolución de ropa" en vez de "cambio de opinión")
recuperara una sección diferente del documento, cambiando la decisión
final de `aprobar` a `requiere_autorizacion_humana` para un caso que
debería haberse aprobado directamente.

Se aplicó `temperature=0` en la llamada del agente como mitigación.
Verificado con 5 repeticiones adicionales del mismo caso: la pregunta
formulada al RAG fue idéntica las 5 veces (antes variaba en cada
ejecución), y la decisión final se mantuvo estable. El razonamiento en
texto libre siguió variando ligeramente incluso con `temperature=0` —
el ajuste reduce la aleatoriedad de forma sustancial, pero no la
elimina por completo.

Esta es una limitación real de los sistemas basados en agentes que no
se ve con RAG básico (una sola llamada, no hay "preguntas intermedias"
que puedan variar): la fiabilidad de un agente depende también de cómo
formula sus propios pasos internos, no solo de la calidad del
razonamiento final.

## Zona gris: reconocimiento de falta de información

Preguntas fuera de dominio (ej. "¿qué coche recomendáis?"): 5/5 (100%)
reconocidas correctamente como sin cobertura — el sistema nunca alucina
ante temas completamente ajenos a los documentos.

Preguntas de zona gris (tema relevante, dato específico no cubierto):
3/5 marcadas como "sin contexto suficiente" en la métrica automática, pero
tras revisión manual, 1 de esas 2 "fallidas" era en realidad una respuesta
correcta por inferencia lógica simple (comparar un plazo dado contra el
documentado). El fallo genuino real es 1/5: ante un caso límite explícito
(descuento del 100% en liquidación), el sistema respondió con confianza
citando una política relacionada, sin marcar la incertidumbre que ese
caso extremo merecía.

**Lección:** `has_sufficient_context` mide bien los extremos (fuera de
dominio vs. dato explícito), pero la métrica automática no distingue
"inferencia válida" de "alucinación real" — requiere revisión manual en
casos límite, no basta con contar el booleano sin más.

## Próximos pasos

- [x] Contextual retrieval (implementado y evaluado — ver sección Evaluación)
- [x] Evals para medir calidad de recuperación (Pass@k + posición media)
- [x] Soporte para múltiples documentos
- [x] Migración de Chroma a pgvector (backend seleccionable)
- [x] Structured outputs con Pydantic
- [x] Agente de conciliación de devoluciones (tool use, Fase 2 del roadmap)
- [x] Guardrail en código para el umbral de 150€ (doble capa: agente + verificación)
- [x] Segunda herramienta para el agente (ej. consultar historial del cliente)
- [x] Extender eval.py con preguntas sin cobertura, para medir la tasa de
      reconocimiento honesto de falta de información (has_sufficient_context)
- [x] Logging estructurado por query (coste, latencia, chunks usados) para
      observabilidad real, no solo evaluación puntual
- [x] Detección y mitigación de no-determinismo en el agente
      (temperature=0)
- [ ] Ampliar la muestra de repeticiones para cuantificar la tasa de
      inconsistencia con más confianza estadística (5 repeticiones es
      evidencia direccional, no concluyente)