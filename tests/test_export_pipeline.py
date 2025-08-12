import shutil
from pathlib import Path

from src.catalog import connect, ensure_schema
from src.exporter import export_conversation_package
from src.text_utils import content_hash, slugify


def setup_temp_output(tmp_dir: Path):
    if tmp_dir.exists():
        shutil.rmtree(tmp_dir)
    tmp_dir.mkdir(parents=True)

def test_slugify_edge_cases():
    assert slugify("") == "untitled"
    assert slugify("   ") == "untitled"
    assert slugify("Hello World!") == "hello-world"
    assert slugify("Multi   Space   Test") == "multi-space-test"
    assert slugify("Symbols*&^%$#@!and--Dashes") == "symbols-and-dashes"

def test_content_hash_stability():
    a = content_hash("Hello   World")
    b = content_hash("  hello world  ")
    assert a == b

def test_export_and_skip(tmp_path):
    output_dir = tmp_path / "output"
    setup_temp_output(output_dir)
    db_path = tmp_path / "catalog.sqlite"
    ensure_schema(str(db_path))

    conversation = {
        "graph_id": "chat-1",
        "title": "Sample Conversation",
        "url": "https://example.com/chat/1",
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-01-01T00:00:00Z",
    }
    messages = [
        {
            "graph_id": "chat-1-msg-1",
            "author": "user",
            "role": "user",
            "content": "Hello bot",
            "created_at": "2025-01-01T00:00:01Z",
            "updated_at": "2025-01-01T00:00:01Z",
        },
        {
            "graph_id": "chat-1-msg-2",
            "author": "assistant",
            "role": "assistant",
            "content": "Hello human",
            "created_at": "2025-01-01T00:00:02Z",
            "updated_at": "2025-01-01T00:00:02Z",
        },
    ]

    with connect(str(db_path)) as conn:
        res1 = export_conversation_package(conn, str(output_dir), conversation.copy(), [m.copy() for m in messages])
        assert not res1["skipped"]
        res2 = export_conversation_package(conn, str(output_dir), conversation.copy(), [m.copy() for m in messages])
        assert res2["skipped"]

    messages[1]["content"] = "Hello human updated"
    conversation["updated_at"] = "2025-01-01T00:10:00Z"
    with connect(str(db_path)) as conn:
        res3 = export_conversation_package(conn, str(output_dir), conversation.copy(), [m.copy() for m in messages])
        assert not res3["skipped"]
        assert not res3["skipped"]
