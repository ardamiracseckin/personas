"""eval/questions.json üzerinden regresyon: soru seti sağlam mı, yönlendirme doğru mu.

Yönlendirme kontrolü LLM gerektirmez, milisaniyeler sürer. Erişim kontrolü ingest
edilmiş veritabanı ve embedding modeli gerektirdiği için veritabanı boşsa atlanır.
"""
import json
from pathlib import Path

import pytest

from app import config, router, store

QUESTIONS_PATH = Path(__file__).resolve().parent.parent / "eval" / "questions.json"
QUESTIONS = json.loads(QUESTIONS_PATH.read_text(encoding="utf-8"))["questions"]
CATEGORIES = {"cevaplanabilir", "cevaplanamaz", "uc_durum", "yonlendirme", "yazim_hatasi"}


def by_category(name):
    return [q for q in QUESTIONS if q["category"] == name]


def test_question_set_is_well_formed():
    ids = [q["id"] for q in QUESTIONS]
    assert len(ids) == len(set(ids)), "soru kimlikleri benzersiz olmalı"
    assert {q["category"] for q in QUESTIONS} <= CATEGORIES
    assert all(q["expected_source"] for q in by_category("cevaplanabilir"))
    assert all(q["expected_source"] for q in by_category("yazim_hatasi"))
    assert all(q["expected_route"] for q in by_category("yonlendirme"))


@pytest.mark.parametrize("q", by_category("yonlendirme"), ids=lambda q: q["id"])
def test_routing_matches_expectation(q):
    assert router.route(q["question"]) == q["expected_route"]


@pytest.mark.parametrize("q", by_category("cevaplanabilir") + by_category("yazim_hatasi"),
                         ids=lambda q: q["id"])
def test_documents_questions_are_not_hijacked_by_tools(q):
    # Belge soruları yanlışlıkla takvim/mail/uygulama aracına gitmemeli.
    assert router.route(q["question"]) == {"tool": "documents", "action": "read"}


@pytest.mark.slow
@pytest.mark.skipif(not config.DB_PATH.exists() or store.count() == 0,
                    reason="ingest edilmiş veritabanı yok ('python -m app.ingest')")
def test_expected_source_is_retrieved_for_every_answerable_question():
    from app import retriever

    for q in by_category("cevaplanabilir"):
        sources = [src for (src, _text, _score) in retriever.get_top_chunks(q["question"])]
        assert q["expected_source"] in sources, f"{q['id']}: {q['question']}"


@pytest.mark.slow
@pytest.mark.skipif(not config.DB_PATH.exists() or store.count() == 0,
                    reason="ingest edilmiş veritabanı yok ('python -m app.ingest')")
def test_misspelled_questions_still_reach_their_source():
    """Hibrit erişimin varlık sebebi: bozuk yazım doğru belgeyi bulmalı."""
    from app import retriever

    kacan = []
    for q in by_category("yazim_hatasi"):
        sources = [src for (src, _text, _score) in retriever.get_top_chunks(q["question"])]
        if q["expected_source"] not in sources:
            kacan.append(q["id"])
    # Tamamı tutmayabilir; ölçüm docs/eval içinde raporlanır. Çoğunluk şart.
    assert len(kacan) <= 3, f"yazım hatalı sorularda kaçan: {kacan}"


# --- otomatik kalite puanlaması --------------------------------------------

def test_every_answerable_question_has_expected_substrings():
    assert all(q.get("expected_substrings") for q in by_category("cevaplanabilir"))


def test_quality_score_levels():
    from scripts.evaluate import quality_score

    beklenen = ["git reset --soft", "HEAD~1"]
    assert quality_score("git reset --soft HEAD~1 kullanılır", beklenen) == 2
    assert quality_score("git reset --soft yeterli", beklenen) == 1
    assert quality_score("git restore kullanın", beklenen) == 0
    assert quality_score("herhangi bir cevap", None) is None


def test_quality_score_ignores_spacing():
    from scripts.evaluate import quality_score

    assert quality_score("Cmd+Shift+4 tuşlarına basın", ["Cmd + Shift + 4"]) == 2
