import json
import os
from typing import Any, Dict, Iterable, Iterator


def write_jsonl(path: str, records: Iterable[Dict[str, Any]]) -> None:
    """Write iterable of dict records to JSONL file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def read_jsonl(path: str) -> Iterator[Dict[str, Any]]:
    """Stream records from a JSONL file."""
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)
