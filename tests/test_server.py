"""HTTP katmanı: sohbet akışı (SSE), konuşma/belge/model uç noktaları.

Model çağrılmaz; assistant ve models katmanları sahte davranışlarla değiştirilir.
"""
import json

import pytest
from fastapi.testclient import TestClient

import app.config as config
from app import chat_store, store


@pytest.fixture
def istemci(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "t.db")
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    monkeypatch.setattr(config, "DOCUMENTS_DIR", tmp_path / "belgeler")
    store.init_db()
    chat_store.init_db()
    from server import main

    return TestClient(main.app)


def sse_olaylari(response):
    return [json.loads(s[len("data: "):]) for s in response.text.splitlines()
            if s.startswith("data: ")]


def sahte_akis(monkeypatch, tokens=("Mer", "haba"), sources=("git-notlari.md",), pending=None):
    from server import main

    def _stream(query, deps=None, history=None):
        for t in tokens:
            yield {"type": "token", "text": t}
        yield {"type": "final", "result": {
            "text": "".join(tokens), "sources": list(sources), "pending_action": pending,
            "chunks": [{"source": s, "text": f"{s} içeriği", "score": 0.9} for s in sources]}}

    monkeypatch.setattr(main.assistant, "answer_stream", _stream)
    monkeypatch.setattr(main, "generate_title", lambda metin: "Kısa başlık")


# --- konuşmalar -------------------------------------------------------------

def test_conversation_crud(istemci):
    olustur = istemci.post("/api/conversations", json={}).json()
    assert olustur["id"] and olustur["title"]

    istemci.patch(f"/api/conversations/{olustur['id']}", json={"title": "Git soruları"})
    liste = istemci.get("/api/conversations").json()
    assert liste[0]["title"] == "Git soruları"

    istemci.delete(f"/api/conversations/{olustur['id']}")
    assert istemci.get("/api/conversations").json() == []


def test_messages_are_returned_in_order(istemci):
    cid = istemci.post("/api/conversations", json={}).json()["id"]
    chat_store.add_message(cid, "user", "soru")
    chat_store.add_message(cid, "assistant", "cevap", ["a.md"])
    mesajlar = istemci.get(f"/api/conversations/{cid}/messages").json()
    assert [m["role"] for m in mesajlar] == ["user", "assistant"]
    assert mesajlar[1]["sources"] == ["a.md"]


# --- sohbet akışı -----------------------------------------------------------

def test_chat_streams_tokens_then_final(istemci, monkeypatch):
    sahte_akis(monkeypatch)
    cid = istemci.post("/api/conversations", json={}).json()["id"]
    cevap = istemci.post("/api/chat", json={"conversation_id": cid, "message": "selam"})
    assert cevap.status_code == 200

    olaylar = sse_olaylari(cevap)
    assert [o["type"] for o in olaylar if o["type"] == "token"] == ["token", "token"]
    final = next(o for o in olaylar if o["type"] == "final")
    assert final["result"]["text"] == "Merhaba"
    assert final["result"]["chunks"][0]["text"] == "git-notlari.md içeriği"


def test_chat_persists_both_messages(istemci, monkeypatch):
    sahte_akis(monkeypatch)
    cid = istemci.post("/api/conversations", json={}).json()["id"]
    istemci.post("/api/chat", json={"conversation_id": cid, "message": "selam"})
    kayitli = chat_store.get_messages(cid)
    assert [m["role"] for m in kayitli] == ["user", "assistant"]
    assert kayitli[1]["sources"] == ["git-notlari.md"]


def test_first_exchange_names_the_conversation(istemci, monkeypatch):
    sahte_akis(monkeypatch)
    cid = istemci.post("/api/conversations", json={}).json()["id"]
    cevap = istemci.post("/api/chat", json={"conversation_id": cid, "message": "selam"})
    assert any(o["type"] == "title" for o in sse_olaylari(cevap))
    assert istemci.get("/api/conversations").json()[0]["title"] == "Kısa başlık"


def test_regenerate_drops_the_previous_answer(istemci, monkeypatch):
    sahte_akis(monkeypatch)
    cid = istemci.post("/api/conversations", json={}).json()["id"]
    istemci.post("/api/chat", json={"conversation_id": cid, "message": "selam"})
    istemci.post("/api/chat", json={"conversation_id": cid, "regenerate": True})
    kayitli = chat_store.get_messages(cid)
    assert [m["role"] for m in kayitli] == ["user", "assistant"]  # tekrar eklenmedi


def test_missing_conversation_is_rejected(istemci, monkeypatch):
    sahte_akis(monkeypatch)
    cevap = istemci.post("/api/chat", json={"conversation_id": 999, "message": "selam"})
    assert cevap.status_code == 404


def test_model_error_becomes_an_error_event(istemci, monkeypatch):
    from server import main

    def _patla(query, deps=None, history=None):
        raise RuntimeError("Foundry Local'e ulaşılamadı")
        yield  # pragma: no cover

    monkeypatch.setattr(main.assistant, "answer_stream", _patla)
    cid = istemci.post("/api/conversations", json={}).json()["id"]
    olaylar = sse_olaylari(istemci.post("/api/chat", json={"conversation_id": cid, "message": "s"}))
    hata = next(o for o in olaylar if o["type"] == "error")
    assert "Foundry" in hata["message"]


# --- belgeler ---------------------------------------------------------------

def test_document_upload_and_list(istemci, monkeypatch):
    from server import main

    monkeypatch.setattr(main.ingest, "ingest_file",
                        lambda yol, **kw: store.add_chunk(yol.name, "içerik", [1.0]) or 1)
    cevap = istemci.post("/api/documents",
                         files={"file": ("notlar.md", b"# Baslik\n\nicerik", "text/markdown")})
    assert cevap.status_code == 200 and cevap.json()["chunks"] == 1
    assert istemci.get("/api/documents").json()[0]["name"] == "notlar.md"


def test_unsupported_document_is_rejected(istemci):
    cevap = istemci.post("/api/documents",
                         files={"file": ("resim.png", b"\x89PNG", "image/png")})
    assert cevap.status_code == 400


def test_document_delete(istemci, monkeypatch):
    store.add_chunk("eski.md", "içerik", [1.0])
    istemci.delete("/api/documents/eski.md")
    assert istemci.get("/api/documents").json() == []


# --- modeller ---------------------------------------------------------------

def test_model_list_and_switch(istemci, monkeypatch):
    from server import main

    monkeypatch.setattr(main.models, "catalog", lambda: [{"alias": "phi-4-mini", "aktif": True}])
    secilen = {}
    monkeypatch.setattr(main.models, "switch", lambda a: secilen.setdefault("alias", a) or a)

    assert istemci.get("/api/models").json()[0]["alias"] == "phi-4-mini"
    assert istemci.post("/api/models", json={"alias": "qwen2.5-1.5b"}).status_code == 200
    assert secilen["alias"] == "qwen2.5-1.5b"


def test_failed_model_switch_reports_the_reason(istemci, monkeypatch):
    from server import main

    def _patla(alias):
        raise RuntimeError("genai_config.json ayrıştırılamadı")

    monkeypatch.setattr(main.models, "switch", _patla)
    cevap = istemci.post("/api/models", json={"alias": "qwen3-vl-2b-instruct"})
    assert cevap.status_code == 400
    assert "genai_config" in cevap.json()["detail"]


def test_index_page_is_served(istemci):
    sayfa = istemci.get("/")
    assert sayfa.status_code == 200
    assert "personas" in sayfa.text
