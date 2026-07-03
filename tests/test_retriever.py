import app.config as config
from app import retriever, store


def test_returns_most_similar_above_threshold(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "t.db")
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    monkeypatch.setattr(config, "SIM_THRESHOLD", 0.0)
    store.init_db()
    store.clear()
    store.add_chunk("d", "kediler", [1.0, 0.0])
    store.add_chunk("d", "köpekler", [0.0, 1.0])
    res = retriever.get_top_chunks("q", k=1, embed_fn=lambda t: [[1.0, 0.0]])
    assert res[0][1] == "kediler"
    assert res[0][2] > 0.99


def test_threshold_filters_everything(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "t.db")
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    monkeypatch.setattr(config, "SIM_THRESHOLD", 0.99)
    store.init_db()
    store.clear()
    store.add_chunk("d", "kediler", [1.0, 0.0])
    res = retriever.get_top_chunks("q", embed_fn=lambda t: [[0.0, 1.0]])
    assert res == []
