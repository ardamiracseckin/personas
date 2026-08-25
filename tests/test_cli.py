"""CLI çıktısı: cevabın altındaki kaynak ve atıf satırları.

Terminalde cevap akarak yazıldığı için rozet metnin içine konamaz; bunun yerine
cevabın altına cümle sırasına göre bir atıf haritası yazılır. Numaralar web
arayüzündeki rozetlerle aynıdır (parça sırası).
"""
from ui import cli

PARCALAR = [
    {"source": "python-notlari.md", "score": 0.72,
     "text": "Sanal ortam `python3 -m venv .venv` ile oluşturulur."},
    {"source": "vscode-notlari.md", "score": 0.41,
     "text": "Projede arama için `Cmd + Shift + F` kullanılır."},
]


def _sonuc(text, chunks=PARCALAR, sources=None):
    from app import citations
    return {"text": text, "chunks": chunks,
            "sources": sources if sources is not None else [c["source"] for c in chunks],
            "pending_action": None, "citations": citations.attribute(text, chunks)}


def test_document_answer_lists_numbered_sources():
    satirlar = cli.citation_lines(_sonuc("Sanal ortam `python3 -m venv .venv` ile oluşturulur."))
    assert "[1] python-notlari.md" in satirlar[0]
    assert "[2] vscode-notlari.md" in satirlar[0]


def test_each_sentence_is_mapped_to_its_source_number():
    cevap = ("Sanal ortam `python3 -m venv .venv` ile oluşturulur. "
             "Projede arama için `Cmd + Shift + F` kullanılır.")
    harita = cli.citation_lines(_sonuc(cevap))[1]
    assert "1→[1]" in harita
    assert "2→[2]" in harita


def test_unattributed_sentences_are_named():
    cevap = ("Sanal ortam `python3 -m venv .venv` ile oluşturulur. "
             "Docker imajı `docker build` ile üretilir.")
    harita = cli.citation_lines(_sonuc(cevap))[1]
    assert "atıfsız: 2" in harita


def test_answers_without_chunks_keep_the_plain_source_line():
    satirlar = cli.citation_lines(_sonuc("Bugün iki etkinliğin var.", chunks=[],
                                         sources=["Apple Takvim"]))
    assert satirlar == ["  (Kaynak: Apple Takvim)"]


def test_answers_without_sources_print_nothing():
    assert cli.citation_lines(_sonuc("Merhaba.", chunks=[], sources=[])) == []
