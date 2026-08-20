import pytest

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


# --- tek dosya, artımlı yükleme (arayüzden sürükle-bırak için) --------------

def _sahte_embed(chunks):
    return [[1.0, 0.0] for _ in chunks]


def _gecici_db(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "t.db")
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    store.init_db()
    store.clear()


def test_ingest_file_adds_only_that_document(tmp_path, monkeypatch):
    _gecici_db(tmp_path, monkeypatch)
    store.add_chunk("baska.md", "önceki belge", [1.0, 0.0])
    dosya = tmp_path / "yeni.md"
    dosya.write_text("## Başlık\n\nBirinci paragraf.\n\n## İkinci\n\nİkinci paragraf.", encoding="utf-8")

    sayi = ingest.ingest_file(dosya, embed_fn=_sahte_embed)
    assert sayi == 2
    kaynaklar = dict(store.sources())
    assert kaynaklar == {"baska.md": 1, "yeni.md": 2}


def test_reingesting_a_file_replaces_its_chunks(tmp_path, monkeypatch):
    _gecici_db(tmp_path, monkeypatch)
    dosya = tmp_path / "not.md"
    dosya.write_text("## A\n\nbir\n\n## B\n\niki", encoding="utf-8")
    ingest.ingest_file(dosya, embed_fn=_sahte_embed)
    dosya.write_text("## A\n\ntek bölüm kaldı", encoding="utf-8")
    ingest.ingest_file(dosya, embed_fn=_sahte_embed)
    assert dict(store.sources()) == {"not.md": 1}


def test_unsupported_extension_is_rejected(tmp_path, monkeypatch):
    _gecici_db(tmp_path, monkeypatch)
    dosya = tmp_path / "resim.png"
    dosya.write_bytes(b"\x89PNG")
    with pytest.raises(ValueError):
        ingest.ingest_file(dosya, embed_fn=_sahte_embed)


def test_pdf_goes_through_the_pdf_reader(tmp_path, monkeypatch):
    _gecici_db(tmp_path, monkeypatch)
    dosya = tmp_path / "belge.pdf"
    dosya.write_bytes(b"%PDF-1.4")
    monkeypatch.setattr(ingest, "_read_pdf", lambda p: "## Bölüm\n\nPDF içeriği burada.")
    assert ingest.ingest_file(dosya, embed_fn=_sahte_embed) == 1
    assert dict(store.sources()) == {"belge.pdf": 1}
