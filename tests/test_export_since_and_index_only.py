import os
from types import SimpleNamespace

from scripts.export_cli import run_index_only
from src.catalog import connect, ensure_schema
from src.exporter import export_conversation_package


def _make_conv(idx: int, updated: str):
    return {
        "graph_id": f"conv-{idx}",
        "title": f"Conversation {idx}",
        "url": f"https://example.com/chat/{idx}",
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": updated,
    }


def _make_messages(idx: int, updated: str):
    return [
        {
            "graph_id": f"conv-{idx}-m1",
            "author": "user",
            "role": "user",
            "content": f"Hello from {idx}",
            "created_at": "2025-01-01T00:00:01Z",
            "updated_at": updated,
        }
    ]


def test_since_filter_and_index_only(tmp_path):
    output_dir = tmp_path / "out"
    output_dir.mkdir()
    db_path = tmp_path / "catalog.sqlite"
    ensure_schema(str(db_path))

    conv1 = _make_conv(1, "2025-01-01T00:00:10Z")
    conv2 = _make_conv(2, "2025-01-01T00:05:00Z")
    messages1 = _make_messages(1, "2025-01-01T00:00:10Z")
    messages2 = _make_messages(2, "2025-01-01T00:05:00Z")

    with connect(str(db_path)) as conn:
        res1 = export_conversation_package(
            conn,
            str(output_dir),
            conv1.copy(),
            [m.copy() for m in messages1],
        )
        assert not res1["skipped"]
        res2 = export_conversation_package(
            conn,
            str(output_dir),
            conv2.copy(),
            [m.copy() for m in messages2],
        )
        assert not res2["skipped"]

    # since filter should skip conv1 but not conv2
    since_iso = "2025-01-01T00:01:00Z"
    with connect(str(db_path)) as conn:
        res_since1 = export_conversation_package(
            conn,
            str(output_dir),
            conv1.copy(),
            [m.copy() for m in messages1],
            since_iso=since_iso,
        )
        res_since2 = export_conversation_package(
            conn,
            str(output_dir),
            conv2.copy(),
            [m.copy() for m in messages2],
            since_iso=since_iso,
        )
    assert res_since1["skipped"] and res_since1["reason"] == "since-filter"
    assert not res_since2["skipped"]

    # remove DB and rebuild via index-only
    os.remove(db_path)

    args = SimpleNamespace(
        db_path=str(db_path),
        output_dir=str(output_dir),
        index_only=True,
    )
    run_index_only(args)

    with connect(str(db_path)) as conn:
        cur = conn.execute("SELECT COUNT(*) FROM conversations")
        count = cur.fetchone()[0]
    # two conversations should be re-indexed
    assert count == 2
