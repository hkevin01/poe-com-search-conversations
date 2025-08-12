import hashlib
import re
from datetime import datetime, timezone
from typing import Optional

_slug_re = re.compile(r"[^a-z0-9]+")
_ws_re = re.compile(r"\s+")

def slugify(text: str, max_len: int = 64) -> str:
    t = (text or "").strip().lower()
    t = _slug_re.sub("-", t)
    t = t.strip("-")
    if not t:
        t = "untitled"
    return t[:max_len].strip("-")

def normalize_for_hash(text: str) -> str:
    return _ws_re.sub(" ", (text or "").strip()).lower()

def content_hash(text: str) -> str:
    return hashlib.sha256(normalize_for_hash(text).encode("utf-8")).hexdigest()

def count_words(text: str) -> int:
    if not text:
        return 0
    return len(_ws_re.sub(" ", text.strip()).split(" "))

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def parse_iso(ts: Optional[str]) -> Optional[datetime]:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except Exception:
        return None
