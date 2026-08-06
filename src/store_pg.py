import os
import psycopg
from pgvector.psycopg import register_vector
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    """"
    Abre una conexión a Posgres y registra el tipo `vector` para que 
    pyscopg sepa convertir listas de Python en tipo VECTOR de pgvector
    """

    conn = psycopg.connect(os.getenv("POSTGRES_URL"))
    register_vector(conn)
    return conn

def store_chunks(
    chunks: list[str],
    embeddings: list[list[float]],
    doc_id: str,
    source: str = "baseline",
    contexts: list[str] | None = None
) -> None:
    """
    Guarda los chunks y sus embeddings en Postgres.
    `source` distingue entre contextual y baseline
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                chunk_id = f"{doc_id}_chunk_{i}_{source}"
                context = contexts[i] if contexts else None
                cur.execute(
                    """
                    INSERT INTO chunks (id, doc_id, content, embedding, context, source)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE
                    SET content = EXCLUDED.content,
                        embedding = EXCLUDED.embedding,
                        context = EXCLUDED.context
                    """,
                    (chunk_id, doc_id, chunk, embedding, context, source)
                )
            conn.commit()
        print(f"{len(chunks)} chunks guardados en Postgres ('{source}') para {doc_id}")

def query_collection(
    query_embedding: list[float],
    n_results: int = 5,
    source: str = "baseline"
) -> list[tuple[str, str]]:
    """
    Busca los n_results chunks más similares (distancia coseno) dentro de un source
    concreto (baseline, contextual).
    Devuelve id y texto
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, content
                FROM chunks
                WHERE source = %s
                ORDER BY embedding <=> %s::vector
                LIMIT %s
                """,
                (source, query_embedding, n_results)
            )
            return cur.fetchall()

