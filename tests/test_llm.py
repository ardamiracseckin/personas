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


class _FakeStreamChat:
    def __init__(self):
        self.completions = self

    def create(self, **kw):
        assert kw["stream"] is True
        def parca(text):
            return type("C", (), {"choices": [type("Ch", (), {
                "delta": type("D", (), {"content": text})})]})
        return iter([parca("Mer"), parca("haba"), parca(None)])


class _FakeStreamClient:
    def __init__(self):
        self.chat = _FakeStreamChat()


def test_chat_stream_yields_content_deltas(monkeypatch):
    monkeypatch.setattr(llm, "_client", lambda: (_FakeStreamClient(), "model-id"))
    assert list(llm.chat_stream("sys", "soru")) == ["Mer", "haba"]


def test_messages_without_image_is_plain_text():
    m = llm._messages("sys", "soru")
    assert m[1]["content"] == "soru"


def test_messages_with_image_becomes_content_array():
    m = llm._messages("sys", "bu görselde ne var?", image_b64="QUJD")
    parcalar = m[1]["content"]
    assert parcalar[0] == {"type": "text", "text": "bu görselde ne var?"}
    assert parcalar[1]["image_url"]["url"].startswith("data:image/jpeg;base64,QUJD")


def test_reset_clears_cached_client(monkeypatch):
    monkeypatch.setattr(llm, "_openai", object())
    monkeypatch.setattr(llm, "_model_id", "eski-model")
    llm.reset()
    assert llm._openai is None and llm._model_id is None


# --- sorgu / belge ayrımı ----------------------------------------------------

def test_e5_models_get_their_required_prefixes(monkeypatch):
    """E5 ailesi sorguyu ve belgeyi farklı ön eklerle bekler.

    Bu asimetri modelin erişim gücünün yarısıdır: aynı metin "query:" ile
    sorulduğunda ve "passage:" ile saklandığında farklı vektörler üretir.
    Ön ek verilmezse model, eğitildiğinden başka bir işte kullanılmış olur.
    """
    from app import config, llm

    gonderilen = []
    monkeypatch.setattr(config, "EMBED_MODEL", "intfloat/multilingual-e5-large")
    monkeypatch.setattr(llm, "_embed_raw", lambda metinler: gonderilen.extend(metinler) or
                        [[0.0] for _ in metinler])
    llm.embed_passages(["kanun metni"])
    llm.embed_query("soru")
    assert gonderilen == ["passage: kanun metni", "query: soru"]


def test_models_without_prefix_convention_are_left_alone(monkeypatch):
    from app import config, llm

    gonderilen = []
    monkeypatch.setattr(config, "EMBED_MODEL",
                        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    monkeypatch.setattr(llm, "_embed_raw", lambda metinler: gonderilen.extend(metinler) or
                        [[0.0] for _ in metinler])
    llm.embed_passages(["kanun metni"])
    llm.embed_query("soru")
    assert gonderilen == ["kanun metni", "soru"]


def test_embed_query_returns_a_flat_vector(monkeypatch):
    from app import llm
    monkeypatch.setattr(llm, "_embed_raw", lambda metinler: [[1.0, 2.0] for _ in metinler])
    assert llm.embed_query("soru") == [1.0, 2.0]
