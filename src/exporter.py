import os
from typing import Any, Dict, List, Optional

from .catalog import upsert_conversation, upsert_message
from .jsonl_io import write_jsonl
from .text_utils import content_hash, count_words, now_iso, parse_iso, slugify


def ensure_paths(base_output: str, conv_slug: str):
    conv_dir = os.path.join(base_output, conv_slug)
    assets_dir = os.path.join(conv_dir, "assets")
    os.makedirs(assets_dir, exist_ok=True)
    return conv_dir, assets_dir

def render_markdown(conversation: Dict[str, Any], messages: List[Dict[str, Any]]) -> str:
    parts = [f"# {conversation.get('title','Untitled Conversation')}"]
    for m in messages:
        ts = m.get("created_at", "") or ""
        author = m.get("author") or m.get("role") or "unknown"
        parts.append(f"\n## [{m.get('ordinal', 0)}] {author} — {ts}\n")
        parts.append(m.get("content", ""))
    return "\n".join(parts).strip() + "\n"

def should_skip(existing: Optional[Dict[str, Any]], updated_at: Optional[str], new_hash: str) -> bool:
    if not existing:
        return False
    prev_hash = existing.get("content_hash")
    if prev_hash and prev_hash == new_hash:
        return True
    prev_updated = parse_iso(existing.get("updated_at"))
    new_updated = parse_iso(updated_at)
    if prev_updated and new_updated and new_updated <= prev_updated:
        return True
    return False

def compute_message_excerpt(text: str, max_chars: int = 180) -> str:
    t = " ".join((text or "").strip().split())
    return t if len(t) <= max_chars else t[: max_chars - 1] + "…"

def export_conversation_package(
    conn,
    base_output: str,
    conversation: Dict[str, Any],
    messages: List[Dict[str, Any]],
    build_db: bool = True,
    since_iso: Optional[str] = None,
    index_only: bool = False,
) -> Dict[str, Any]:
    conv_graph_id = conversation["graph_id"]
    conv_title = conversation.get("title") or "Untitled Conversation"
    conv_slug = conversation.get("slug") or slugify(conv_title)
    conversation["slug"] = conv_slug

    if since_iso:
        since_dt = parse_iso(since_iso)
        conv_updated = parse_iso(conversation.get("updated_at"))
        if since_dt and conv_updated and conv_updated < since_dt:
            return {"graph_id": conv_graph_id, "skipped": True, "reason": "since-filter"}

    conv_dir, assets_dir = ensure_paths(base_output, conv_slug)
    md_path = os.path.join(conv_dir, "conversation.md")
    merged_jsonl_path = os.path.join(conv_dir, "merged.jsonl")

    for idx, m in enumerate(messages, start=1):
        m["ordinal"] = m.get("ordinal", idx)
        msg_title_fallback = (m.get("title") or m.get("content") or "").strip().split("\n")[0][:80] or f"message-{idx}"
        m["slug"] = m.get("slug") or slugify(f"{m['ordinal']:03d}-{msg_title_fallback}")
        m["graph_id"] = m["graph_id"]
        m["conversation_graph_id"] = conv_graph_id
        m["word_count"] = count_words(m.get("content") or "")
        m["content_hash"] = content_hash(m.get("content") or "")
        m["excerpt"] = compute_message_excerpt(m.get("content") or "")
        m["export_md_path"] = os.path.join(conv_dir, f"{m['slug']}.md")
        m["export_assets_path"] = assets_dir
        m["parent_graph_id"] = messages[idx - 2]["graph_id"] if idx > 1 else conversation.get("parent_graph_id")

    conv_text_concat = "\n\n".join(m.get("content") or "" for m in messages)
    conv_hash = content_hash(conv_text_concat)
    conv_word_count = sum(m["word_count"] for m in messages)

    existing_conv = None
    if build_db and not index_only and conn:
        cur = conn.execute("SELECT content_hash, updated_at FROM conversations WHERE graph_id = ?", (conv_graph_id,))
        row = cur.fetchone()
        if row:
            existing_conv = {"content_hash": row[0], "updated_at": row[1]}

    if should_skip(existing_conv, conversation.get("updated_at"), conv_hash):
        return {"graph_id": conv_graph_id, "skipped": True, "reason": "unchanged"}

    if not index_only:
        md_text = render_markdown(conversation, messages)
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_text)

    merged_records: List[Dict[str, Any]] = []
    for m in messages:
        merged_records.append({
            "type": "message",
            "conversation_graph_id": conv_graph_id,
            "graph_id": m["graph_id"],
            "title": m.get("title"),
            "section_title": m.get("title"),
            "section_slug": m["slug"],
            "ordinal": m["ordinal"],
            "author": m.get("author"),
            "role": m.get("role"),
            "created_at": m.get("created_at"),
            "updated_at": m.get("updated_at"),
            "parent_graph_id": m.get("parent_graph_id"),
            "export_paths": {
                "md": m.get("export_md_path"),
                "assets": m.get("export_assets_path"),
            },
            "content_hash": m["content_hash"],
            "word_count": m["word_count"],
            "excerpt": m["excerpt"],
            "content": m.get("content"),
        })
    write_jsonl(merged_jsonl_path, merged_records)

    for m in messages:
        section_dir = os.path.join(conv_dir, m["slug"])
        os.makedirs(section_dir, exist_ok=True)
        section_jsonl_path = os.path.join(section_dir, "section.jsonl")
        write_jsonl(section_jsonl_path, [{
            "type": "message",
            "conversation_graph_id": conv_graph_id,
            "graph_id": m["graph_id"],
            "section_title": m.get("title"),
            "section_slug": m["slug"],
            "ordinal": m["ordinal"],
            "created_at": m.get("created_at"),
            "updated_at": m.get("updated_at"),
            "export_paths": {
                "md": m.get("export_md_path"),
                "assets": m.get("export_assets_path"),
            },
            "content_hash": m["content_hash"],
            "word_count": m["word_count"],
            "excerpt": m["excerpt"],
        }])

    if build_db and conn:
        now = now_iso()
        conv_record = {
            "graph_id": conv_graph_id,
            "title": conv_title,
            "slug": conv_slug,
            "url": conversation.get("url"),
            "created_at": conversation.get("created_at"),
            "updated_at": conversation.get("updated_at"),
            "parent_graph_id": conversation.get("parent_graph_id"),
            "export_md_path": md_path,
            "export_assets_path": assets_dir,
            "content_hash": conv_hash,
            "word_count": conv_word_count,
            "page_order": conversation.get("page_order"),
            "last_indexed_at": now,
        }
        upsert_conversation(conn, conv_record)
        for m in messages:
            msg_record = {
                "graph_id": m["graph_id"],
                "conversation_graph_id": conv_graph_id,
                "title": m.get("title"),
                "slug": m["slug"],
                "author": m.get("author"),
                "role": m.get("role"),
                "ordinal": m["ordinal"],
                "created_at": m.get("created_at"),
                "updated_at": m.get("updated_at"),
                "parent_graph_id": m.get("parent_graph_id"),
                "export_md_path": m.get("export_md_path"),
                "export_assets_path": m.get("export_assets_path"),
                "content_hash": m["content_hash"],
                "word_count": m["word_count"],
                "excerpt": m["excerpt"],
                "last_indexed_at": now,
            }
            upsert_message(conn, msg_record)

    return {
        "graph_id": conv_graph_id,
        "slug": conv_slug,
        "export_paths": {
            "md": md_path,
            "merged_jsonl": merged_jsonl_path,
            "assets": assets_dir,
        },
        "messages": len(messages),
        "skipped": False,
    }
    }
