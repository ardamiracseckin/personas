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


# --- ölçek: sözlüksel katman aday havuzuna uygulanır -------------------------

def test_lexical_scoring_runs_only_on_the_dense_shortlist(monkeypatch):
    """Sözlüksel eşleşme her parçada değil, kosinüsün getirdiği adaylarda çalışır.

    3.069 parçalık mevzuat bilgi tabanında her parçaya SequenceMatcher
    uygulamak sorgu başına 8,7 saniye sürüyordu; kosinüs aynı işi 0,08 saniyede
    yapıyor. Sözlüksel katman yazım hatası toleransı için gerekli, ama yalnız
    en yakın adaylarda gerekli.
    """
    from app import lexical, retriever, store

    parcalar = [(f"k{i}.md", f"parça metni {i}", [1.0 if i == 0 else 0.01, 0.0])
                for i in range(200)]
    monkeypatch.setattr(store, "all_chunks", lambda: parcalar)

    cagrilar = []
    gercek = lexical.fuzzy_score
    monkeypatch.setattr(lexical, "fuzzy_score",
                        lambda q, t: (cagrilar.append(t), gercek(q, t))[1])

    retriever.get_top_chunks("parça metni 0", embed_fn=lambda m: [[1.0, 0.0]])
    assert len(cagrilar) <= retriever.ADAY_HAVUZU
    assert len(cagrilar) < len(parcalar)


def test_shortlist_still_returns_the_best_chunk(monkeypatch):
    from app import retriever, store

    parcalar = [("dogru.md", "aranan metin", [1.0, 0.0])] + \
               [(f"k{i}.md", f"alakasız {i}", [0.0, 1.0]) for i in range(300)]
    monkeypatch.setattr(store, "all_chunks", lambda: parcalar)
    sonuc = retriever.get_top_chunks("aranan metin", embed_fn=lambda m: [[1.0, 0.0]])
    assert sonuc and sonuc[0][0] == "dogru.md"
