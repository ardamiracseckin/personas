from app.tools import app_launcher


def test_resolve_turkish_alias():
    assert app_launcher.resolve_app_name("not defteri") == "Notes"
    assert app_launcher.resolve_app_name("Hesap Makinesi") == "Calculator"


def test_resolve_passthrough_unknown():
    assert app_launcher.resolve_app_name("Spotify") == "Spotify"


def test_open_app_uses_run_fn_and_returns_resolved():
    cap = {}
    opened = app_launcher.open_app("hesap makinesi", run_fn=lambda a: cap.setdefault("a", a))
    assert opened == "Calculator"
    assert cap["a"] == "Calculator"
