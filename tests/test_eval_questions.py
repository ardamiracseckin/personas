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
CATEGORIES = {"cevaplanabilir", "cevaplanamaz", "uc_durum", "yonlendirme"}


def by_category(name):
    return [q for q in QUESTIONS if q["category"] == name]


def test_question_set_is_well_formed():
    ids = [q["id"] for q in QUESTIONS]
    assert len(ids) == len(set(ids)), "soru kimlikleri benzersiz olmalı"
    assert {q["category"] for q in QUESTIONS} <= CATEGORIES
    assert all(q["expected_source"] for q in by_category("cevaplanabilir"))
    assert all(q["expected_route"] for q in by_category("yonlendirme"))


@pytest.mark.parametrize("q", by_category("yonlendirme"), ids=lambda q: q["id"])
def test_routing_matches_expectation(q):
    assert router.route(q["question"]) == q["expected_route"]


@pytest.mark.parametrize("q", by_category("cevaplanabilir"), ids=lambda q: q["id"])
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
