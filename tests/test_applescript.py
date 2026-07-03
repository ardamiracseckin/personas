import subprocess

import pytest

from app.tools import applescript


def test_run_returns_stdout(monkeypatch):
    def fake_run(cmd, **kw):
        return subprocess.CompletedProcess(cmd, 0, stdout="merhaba\n", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    assert applescript.run('return "x"') == "merhaba"


def test_run_raises_turkish_on_permission(monkeypatch):
    def fake_run(cmd, **kw):
        return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="not authorized")

    monkeypatch.setattr(subprocess, "run", fake_run)
    with pytest.raises(applescript.AppleScriptError) as e:
        applescript.run("bad")
    # Turkish dotted-İ doesn't lowercase to ASCII "i", so assert on stable tokens.
    msg = str(e.value)
    assert "İzin" in msg and "Automation" in msg
