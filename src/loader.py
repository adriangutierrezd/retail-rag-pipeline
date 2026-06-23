def load_document(path: str) -> str:
    """Lee el contenido de un archivo y lo devuelve como string."""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def chunk_document(text: str, chunk_size: int = 500, overlap: int = 100) -> list[str]:
    """
    Trocea el texto en chunks de chunk_size caracteres, 
    con overlap caracteres de solapamiento entre chunks consecutivos
    """
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start += chunk_size - overlap

    return chunks

def load_and_chunk(path: str, chunk_size: int = 500, overlap: int = 100) -> list[str]:
    """Combina carga y trocea en un solo paso."""
    text = load_document(path)
    return chunk_document(text, chunk_size, overlap)
