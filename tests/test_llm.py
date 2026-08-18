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


def test_pick_model_matches_alias_prefix():
    ids = ["qwen2.5-1.5b-instruct-generic-gpu:4", "Phi-4-mini-instruct-generic-gpu:5"]
    assert llm.pick_model(ids, "phi-4-mini") == "Phi-4-mini-instruct-generic-gpu:5"
    assert llm.pick_model(ids, "qwen2.5-1.5b") == "qwen2.5-1.5b-instruct-generic-gpu:4"


def test_pick_model_returns_none_instead_of_falling_back():
    # Yanlış modelle sessizce cevap üretmektense hiç model seçmemek doğrudur.
    assert llm.pick_model(["qwen2.5-1.5b-instruct-generic-gpu:4"], "phi-4-mini") is None
    assert llm.pick_model([], "phi-4-mini") is None
