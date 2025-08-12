import argparse
import glob
import json
import os
from typing import Any, Dict, List

from src.catalog import (connect, ensure_schema, upsert_conversation,
                         upsert_message)
from src.exporter import export_conversation_package

DEFAULT_OUTPUT_DIR = "output"


def parse_args():
    p = argparse.ArgumentParser(
        description=(
            "Export Poe.com conversations with metadata and JSONL, and build "
            "a SQLite catalog."
        )
    )
    p.add_argument(
        "--build-db",
        action="store_true",
        help="Populate/update the catalog while exporting.",
    )
    p.add_argument(
        "--db-path",
        default=os.path.join(DEFAULT_OUTPUT_DIR, "catalog.sqlite"),
        help="Path to SQLite catalog (default ./output/catalog.sqlite).",
    )
    p.add_argument(
        "--since",
        help="Only (re)export pages updated since this ISO8601 timestamp.",
    )
    p.add_argument(
        "--index-only",
        action="store_true",
        help=(
            "Build/update DB from existing output folder without "
            "calling scraper."
        ),
    )
    p.add_argument(
        "--output-dir",
        default=DEFAULT_OUTPUT_DIR,
        help="Output directory (default ./output).",
    )
    return p.parse_args()


def scan_existing_output(output_dir: str) -> List[Dict[str, Any]]:
    results = []
    pattern = os.path.join(output_dir, "*", "merged.jsonl")
    for path in glob.glob(pattern):
        conv_dir = os.path.dirname(path)
        conv_slug = os.path.basename(conv_dir)
        messages = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    messages.append(json.loads(line))
        if not messages:
            continue
        conv_graph_id = messages[0]["conversation_graph_id"]
        updated_times = [
            m.get("updated_at") for m in messages if m.get("updated_at")
        ]
        created_times = [
            m.get("created_at") for m in messages if m.get("created_at")
        ]
        conv_created = min(created_times) if created_times else None
        conv_updated = max(updated_times) if updated_times else None
        text_concat = "\n\n".join(m.get("content") or "" for m in messages)
        from src.text_utils import content_hash, count_words
        conv_hash = content_hash(text_concat)
        wc = count_words(text_concat)
        results.append(
            {
                "graph_id": conv_graph_id,
                "slug": conv_slug,
                "title": messages[0].get("section_title")
                or conv_slug.replace("-", " ").title(),
                "created_at": conv_created,
                "updated_at": conv_updated,
                "merged_jsonl_path": path,
                "assets_dir": os.path.join(conv_dir, "assets"),
                "messages": messages,
                "content_hash": conv_hash,
                "word_count": wc,
            }
        )
    return results


def run_index_only(args):
    ensure_schema(args.db_path)
    with connect(args.db_path) as conn:
        from src.text_utils import now_iso
        now = now_iso()
        scanned = scan_existing_output(args.output_dir)
        for conv in scanned:
            conv_dir = os.path.join(args.output_dir, conv["slug"])
            md_path = os.path.join(conv_dir, "conversation.md")
            upsert_conversation(
                conn,
                {
                    "graph_id": conv["graph_id"],
                    "title": conv["title"],
                    "slug": conv["slug"],
                    "url": None,
                    "created_at": conv["created_at"],
                    "updated_at": conv["updated_at"],
                    "parent_graph_id": None,
                    "export_md_path": (
                        md_path if os.path.exists(md_path) else None
                    ),
                    "export_assets_path": (
                        conv["assets_dir"]
                        if os.path.isdir(conv["assets_dir"])
                        else None
                    ),
                    "content_hash": conv["content_hash"],
                    "word_count": conv["word_count"],
                    "page_order": None,
                    "last_indexed_at": now,
                },
            )
            for m in conv["messages"]:
                upsert_message(
                    conn,
                    {
                        "graph_id": m["graph_id"],
                        "conversation_graph_id": conv["graph_id"],
                        "title": m.get("section_title"),
                        "slug": m.get("section_slug"),
                        "author": m.get("author"),
                        "role": m.get("role"),
                        "ordinal": m.get("ordinal"),
                        "created_at": m.get("created_at"),
                        "updated_at": m.get("updated_at"),
                        "parent_graph_id": m.get("parent_graph_id"),
                        "export_md_path": os.path.join(
                            conv_dir, f"{m.get('section_slug')}.md"
                        ),
                        "export_assets_path": os.path.join(conv_dir, "assets"),
                        "content_hash": m.get("content_hash"),
                        "word_count": m.get("word_count"),
                        "excerpt": m.get("excerpt"),
                        "last_indexed_at": now,
                    },
                )


def get_conversations_from_scraper() -> List[Dict[str, Any]]:
    return []


def main():
    args = parse_args()
    if args.index_only:
        run_index_only(args)
        print("Index-only build complete.")
        return

    ensure_schema(args.db_path)
    conversations = get_conversations_from_scraper()
    with connect(args.db_path if args.build_db else None) as maybe_conn:
        for conv in conversations:
            messages = conv.pop("messages", [])
            res = export_conversation_package(
                conn=maybe_conn,
                base_output=args.output_dir,
                conversation=conv,
                messages=messages,
                build_db=args.build_db,
                since_iso=args.since,
                index_only=False,
            )
            if res.get("skipped"):
                print(
                    "Skipped "
                    f"{conv.get('title') or conv['graph_id']}: "
                    f"{res.get('reason')}"
                )
            else:
                print(
                    "Exported "
                    f"{conv.get('title') or conv['graph_id']} -> "
                    f"{res['export_paths']['md']}"
                )


if __name__ == "__main__":  # pragma: no cover
    main()
