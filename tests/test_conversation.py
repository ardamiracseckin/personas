"""Çok turlu konuşma: takip soruları önceki turu görmeli, cevap akışı çalışmalı."""
from app import assistant

GECMIS = [
    ("user", "Git'te son commit'i nasıl geri alırım?"),
    ("assistant", "git reset --soft HEAD~1 kullanılır."),
]


def deps(**over):
    base = {
        "route": lambda q: {"tool": "documents", "action": "read"},
        "retrieve": lambda q: [("git-notlari.md", "git reset --soft HEAD~1", 0.9)],
        "chat": lambda system, user: "MODEL_CEVABI",
        "chat_stream": lambda system, user: iter(["MODEL", "_", "CEVABI"]),
    }
    base.update(over)
    return base


# --- takip sorusu için sorgu yeniden yazımı --------------------------------

def test_anaphoric_question_is_expanded_with_previous_question():
    q = assistant.retrieval_query("Peki bunu geri almayı nasıl iptal ederim?", GECMIS)
    assert "commit" in q  # önceki soru sorguya katıldı


def test_self_contained_question_is_left_alone():
    q = assistant.retrieval_query("SQLite'ta tablo nasıl oluşturulur?", GECMIS)
    assert q == "SQLite'ta tablo nasıl oluşturulur?"


def test_no_history_means_no_rewrite():
    assert assistant.retrieval_query("Peki bunu nasıl yaparım?", []) == "Peki bunu nasıl yaparım?"


# --- geçmiş isteme giriyor mu ----------------------------------------------

def test_history_is_passed_to_the_model():
    seen = {}
    d = deps(chat=lambda system, user: seen.setdefault("user", user) or "cevap")
    assistant.answer("Peki bunu nasıl geri alırım?", deps=d, history=GECMIS)
    assert "ÖNCEKİ KONUŞMA" in seen["user"]
    assert "git reset --soft" in seen["user"]


def test_history_is_omitted_when_absent():
    seen = {}
    d = deps(chat=lambda system, user: seen.setdefault("user", user) or "cevap")
    assistant.answer("Git nedir?", deps=d)
    assert "ÖNCEKİ KONUŞMA" not in seen["user"]


def test_only_the_last_turns_are_kept():
    uzun = [("user", f"soru {i}") for i in range(10)]
    blok = assistant.history_block(uzun)
    assert "soru 9" in blok and "soru 0" not in blok


# --- akış (streaming) -------------------------------------------------------

def test_stream_yields_tokens_then_final_result():
    olaylar = list(assistant.answer_stream("Kireç nasıl temizlenir?", deps=deps()))
    tokens = [e["text"] for e in olaylar if e["type"] == "token"]
    final = [e for e in olaylar if e["type"] == "final"]
    assert tokens == ["MODEL", "_", "CEVABI"]
    assert len(final) == 1
    assert final[0]["result"]["text"] == "MODEL_CEVABI"
    assert final[0]["result"]["sources"] == ["git-notlari.md"]


def test_stream_short_circuits_without_calling_the_model():
    # Bağlam yoksa model hiç çağrılmamalı; tek olay son sonuç olmalı.
    def patlat(system, user):
        raise AssertionError("model çağrılmamalıydı")

    olaylar = list(assistant.answer_stream(
        "Alakasız", deps=deps(retrieve=lambda q: [], chat_stream=patlat)))
    assert [e["type"] for e in olaylar] == ["final"]
    assert "bilgi" in olaylar[0]["result"]["text"].lower()


def test_stream_write_intent_returns_draft_without_model():
    olaylar = list(assistant.answer_stream(
        "Yarın 15:00 dişçi randevusu ekle",
        deps=deps(route=lambda q: {"tool": "calendar", "action": "write"})))
    assert [e["type"] for e in olaylar] == ["final"]
    assert olaylar[0]["result"]["pending_action"]["type"] == "calendar"
