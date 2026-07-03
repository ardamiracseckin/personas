from app import assistant


def deps(**over):
    base = {
        "route": lambda q: {"tool": "documents", "action": "read"},
        "retrieve": lambda q: [("faq.md", "Kireç için X yapın.", 0.9)],
        "calendar": lambda: [{"title": "Dişçi", "start": "2026-07-04 15:00"}],
        "mail": lambda: [{"subject": "Fatura", "sender": "b@x.com"}],
        "chat": lambda system, user: "MODEL_CEVABI",
    }
    base.update(over)
    return base


def test_document_answer_includes_sources():
    res = assistant.answer("Kireç nasıl temizlenir?", deps=deps())
    assert res["text"] == "MODEL_CEVABI"
    assert res["sources"] == ["faq.md"]
    assert res["pending_action"] is None


def test_document_no_context_says_unknown():
    res = assistant.answer("Alakasız soru", deps=deps(retrieve=lambda q: []))
    assert res["pending_action"] is None
    assert "bilgi" in res["text"].lower()


def test_calendar_read_summarizes():
    res = assistant.answer(
        "Bugün ne var?", deps=deps(route=lambda q: {"tool": "calendar", "action": "read"})
    )
    assert res["text"] == "MODEL_CEVABI"
    assert res["pending_action"] is None


def test_calendar_write_returns_pending_not_executed():
    res = assistant.answer(
        "Yarın 15:00 dişçi randevusu ekle",
        deps=deps(route=lambda q: {"tool": "calendar", "action": "write"}),
    )
    pa = res["pending_action"]
    assert pa["type"] == "calendar"
    assert pa["hour"] == 15 and pa["minute"] == 0
    assert res["text"]


def test_confirm_calendar_calls_create():
    called = {}
    d = deps()
    d["create_event"] = lambda *a, **k: called.setdefault("args", a) or True
    pa = {"type": "calendar", "title": "Dişçi", "year": 2026, "month": 7,
          "day": 4, "hour": 15, "minute": 0, "duration_min": 60}
    msg = assistant.confirm(pa, deps=d)
    assert called["args"][0] == "Dişçi"
    assert "eklendi" in msg.lower()


def test_mail_write_returns_pending():
    res = assistant.answer(
        "a@b.com adresine 'Konu' başlıklı mail gönder: Merhaba",
        deps=deps(route=lambda q: {"tool": "mail", "action": "write"}),
    )
    pa = res["pending_action"]
    assert pa["type"] == "mail" and pa["to"] == "a@b.com"
