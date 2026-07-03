from app.tools import mail_tool


def test_parse_mails():
    raw = "Fatura|bank@x.com\nMerhaba|ali@y.com"
    assert mail_tool.parse_mails(raw) == [
        {"subject": "Fatura", "sender": "bank@x.com"},
        {"subject": "Merhaba", "sender": "ali@y.com"},
    ]


def test_get_recent_uses_run_fn():
    out = mail_tool.get_recent(run_fn=lambda s: "Konu|a@b.com")
    assert out == [{"subject": "Konu", "sender": "a@b.com"}]


def test_send_mail_builds_script():
    cap = {}
    ok = mail_tool.send_mail(
        "a@b.com", "Konu", "Gövde", run_fn=lambda s: cap.setdefault("s", s) or ""
    )
    assert ok is True
    assert "a@b.com" in cap["s"] and "Konu" in cap["s"]
