import app.config as config
from app import ingest, store


def fake_embed(texts):
    return [[float(len(t)), 0.0] for t in texts]


def test_ingest_reads_files_and_stores_chunks(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "t.db")
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    # Small limit so "Bir." and "İki." become separate chunks (tests multi-chunk files).
    monkeypatch.setattr(config, "MAX_CHUNK_CHARS", 4)
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "a.md").write_text("Bir.\n\nİki.")
    (docs / "b.txt").write_text("Üç.")
    store.init_db()
    store.clear()
    n = ingest.ingest_folder(docs, embed_fn=fake_embed)
    assert n == 3
    assert store.count() == 3
    sources = {s for (s, _t, _e) in store.all_chunks()}
    assert sources == {"a.md", "b.txt"}
