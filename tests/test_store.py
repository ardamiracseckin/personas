import app.config as config
from app import store


def test_add_and_read_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "t.db")
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    store.init_db()
    assert store.count() == 0
    store.add_chunk("doc1.md", "hello world", [0.1, 0.2, 0.3])
    assert store.count() == 1
    rows = store.all_chunks()
    assert rows == [("doc1.md", "hello world", [0.1, 0.2, 0.3])]
    store.clear()
    assert store.count() == 0
