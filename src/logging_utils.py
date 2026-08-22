import json
from pathlib import Path
from datetime import datetime, timezone

LOG_PATH = Path("logs/events.jsonl")


def log_event(event_type: str, data: dict) -> None:
    """
    Registra un evento estructurado en logs/events.jsonl.
    Cada línea es un JSON independiente (formato JSON Lines),
    fácil de leer línea a línea o cargar con pandas más adelante.
    """
    LOG_PATH.parent.mkdir(exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        **data,
    }
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
