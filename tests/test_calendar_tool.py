from app.tools import calendar_tool


def test_parse_events():
    raw = "Toplantı|2026-07-03 10:00\nDişçi|2026-07-04 15:00"
    assert calendar_tool.parse_events(raw) == [
        {"title": "Toplantı", "start": "2026-07-03 10:00"},
        {"title": "Dişçi", "start": "2026-07-04 15:00"},
    ]


def test_parse_empty():
    assert calendar_tool.parse_events("") == []


def test_get_events_uses_run_fn():
    out = calendar_tool.get_events(run_fn=lambda script: "X|2026-07-03 09:00")
    assert out == [{"title": "X", "start": "2026-07-03 09:00"}]


def test_create_event_builds_and_runs():
    captured = {}

    def run_fn(script):
        captured["s"] = script
        return ""

    ok = calendar_tool.create_event(
        "Dişçi", 2026, 7, 4, 15, 0, duration_min=60, run_fn=run_fn
    )
    assert ok is True
    assert "Dişçi" in captured["s"]
    assert "make new event" in captured["s"]
