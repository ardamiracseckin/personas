import numpy as np

from app import llm


class _FakeMsg:
    def __init__(self, content):
        self.message = type("M", (), {"content": content})


class _FakeChat:
    def __init__(self):
        self.completions = self

    def create(self, **kw):
        self.kw = kw
        return type("R", (), {"choices": [_FakeMsg("cevap")]})


class _FakeClient:
    def __init__(self):
        self.chat = _FakeChat()


class _FakeEmbedder:
    def embed(self, texts):
        return (np.array([0.1, 0.2]) for _ in texts)


def test_chat_returns_content(monkeypatch):
    monkeypatch.setattr(llm, "_client", lambda: (_FakeClient(), "model-id"))
    assert llm.chat("sys", "soru") == "cevap"


def test_embed_returns_lists(monkeypatch):
    monkeypatch.setattr(llm, "_embedder", lambda: _FakeEmbedder())
    assert llm.embed(["a", "b"]) == [[0.1, 0.2], [0.1, 0.2]]
