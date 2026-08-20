import pytest

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
    # Skor hibrit: 0.75 x kosinüs + 0.25 x sözlüksel. "q" tek harf, sözlüksel katkı 0.
    assert res[0][2] == pytest.approx(config.DENSE_WEIGHT, abs=1e-6)


def test_threshold_filters_everything(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "t.db")
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    monkeypatch.setattr(config, "SIM_THRESHOLD", 0.99)
    store.init_db()
    store.clear()
    store.add_chunk("d", "kediler", [1.0, 0.0])
    res = retriever.get_top_chunks("q", embed_fn=lambda t: [[0.0, 1.0]])
    assert res == []


def test_lexical_layer_rescues_a_misspelled_query(tmp_path, monkeypatch):
    """Embedding aynı skoru verse bile bozuk yazımlı sorgu doğru parçayı bulmalı."""
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "t.db")
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    monkeypatch.setattr(config, "SIM_THRESHOLD", 0.0)
    store.init_db()
    store.clear()
    # git parçası embedding'de kasten daha yakın; yalnızca sözlüksel katman bunu çevirebilir.
    store.add_chunk("macos.md", "Ekran görüntüsü belirli bölge: Cmd + Shift + 4", [1.0, 0.1])
    store.add_chunk("git.md", "Son commit'i geri almak için git reset --soft", [1.0, 0.0])

    res = retriever.get_top_chunks(
        "ekran görünütsünü belirli bölgden nasıl alrım",
        k=1, embed_fn=lambda t: [[1.0, 0.0]])
    assert res[0][0] == "macos.md"


def test_scores_stay_within_unit_range(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "t.db")
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    monkeypatch.setattr(config, "SIM_THRESHOLD", 0.0)
    store.init_db()
    store.clear()
    store.add_chunk("d", "ekran görüntüsü", [1.0, 0.0])
    res = retriever.get_top_chunks("ekran görüntüsü", k=1, embed_fn=lambda t: [[1.0, 0.0]])
    assert 0.0 <= res[0][2] <= 1.0
