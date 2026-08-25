"""Satır içi atıf: cevabın her cümlesi hangi parçadan geliyor.

Model istemine dokunulmaz — atıf, cevap üretildikten sonra sadakat ölçümüyle
aynı sözlüksel eşleştirmeyle çıkarılır. Böylece gecikme artmaz ve gösterdiğimiz
atıf, ölçtüğümüz dayanakla aynı mantığa dayanır.
"""
from app import citations

PARCALAR = [
    {"source": "git-notlari.md", "score": 0.61,
     "text": "Yarım kalan değişiklikleri saklamak için `git stash` çalıştırılır. "
             "Geri getirmek için `git stash pop` kullanılır."},
    {"source": "python-notlari.md", "score": 0.44,
     "text": "Sanal ortam `python3 -m venv .venv` ile oluşturulur, "
             "`source .venv/bin/activate` ile etkinleştirilir."},
]


def _metinler(cevap, konumlar):
    return [cevap[bas:son] for (bas, son) in konumlar]


def test_spans_point_at_the_real_sentences():
    cevap = "Birinci cümle. İkinci cümle."
    assert _metinler(cevap, citations.spans(cevap)) == ["Birinci cümle.", "İkinci cümle."]


def test_dot_inside_a_code_span_does_not_end_the_sentence():
    cevap = "Dosyayı `pip install -r requirements.txt` ile kurarsın."
    assert len(citations.spans(cevap)) == 1


def test_lines_are_separate_units():
    cevap = "- `git stash` saklar\n- `git stash pop` geri getirir"
    assert len(citations.spans(cevap)) == 2


def test_fenced_code_blocks_are_not_cited():
    cevap = "Şunu çalıştır:\n```bash\ngit stash\n```\nSonrası kolay."
    metinler = _metinler(cevap, citations.spans(cevap))
    assert "git stash" not in " ".join(metinler)
    assert "Şunu çalıştır:" in metinler


def test_each_sentence_is_attributed_to_the_chunk_that_supports_it():
    cevap = ("Değişiklikleri saklamak için `git stash` çalıştırılır. "
             "Sanal ortam `python3 -m venv .venv` ile oluşturulur.")
    atiflar = citations.attribute(cevap, PARCALAR)
    assert [a["source"] for a in atiflar] == ["git-notlari.md", "python-notlari.md"]


def test_sentences_without_support_are_left_uncited():
    cevap = "Docker imajı `docker build -t ad .` ile oluşturulur."
    assert citations.attribute(cevap, PARCALAR) == []


def test_attribution_keeps_the_chunk_index_for_the_panel():
    cevap = "Sanal ortam `python3 -m venv .venv` ile oluşturulur."
    atif = citations.attribute(cevap, PARCALAR)[0]
    assert atif["chunk"] == 1
    assert atif["score"] > 0.5


def test_no_chunks_means_no_citations():
    assert citations.attribute("Herhangi bir cevap.", []) == []
