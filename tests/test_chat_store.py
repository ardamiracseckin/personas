"""Kalıcı sohbet: konuşmalar ve mesajlar SQLite'ta durur."""
import pytest

import app.config as config
from app import chat_store


@pytest.fixture(autouse=True)
def gecici_db(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "t.db")
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    chat_store.init_db()


def test_create_and_list():
    birinci = chat_store.create_conversation("Git soruları")
    ikinci = chat_store.create_conversation()
    hepsi = chat_store.list_conversations()
    assert [c["id"] for c in hepsi] == [ikinci, birinci]  # en yeni başta
    assert hepsi[1]["title"] == "Git soruları"
    assert hepsi[0]["title"]  # başlıksız açılan sohbet de bir ada sahip


def test_messages_round_trip():
    cid = chat_store.create_conversation("Deneme")
    chat_store.add_message(cid, "user", "Sanal ortam nasıl kurulur?")
    chat_store.add_message(cid, "assistant", "python3 -m venv .venv", ["python-notlari.md"])
    mesajlar = chat_store.get_messages(cid)
    assert [m["role"] for m in mesajlar] == ["user", "assistant"]
    assert mesajlar[1]["sources"] == ["python-notlari.md"]
    assert mesajlar[0]["sources"] == []


def test_history_pairs_for_the_assistant():
    cid = chat_store.create_conversation()
    chat_store.add_message(cid, "user", "soru")
    chat_store.add_message(cid, "assistant", "cevap")
    assert chat_store.history(cid) == [("user", "soru"), ("assistant", "cevap")]


def test_rename_and_delete():
    cid = chat_store.create_conversation("Eski")
    chat_store.add_message(cid, "user", "merhaba")
    chat_store.rename_conversation(cid, "Yeni")
    assert chat_store.list_conversations()[0]["title"] == "Yeni"
    chat_store.delete_conversation(cid)
    assert chat_store.list_conversations() == []
    assert chat_store.get_messages(cid) == []  # mesajlar da silinir


def test_new_message_bumps_the_conversation_to_the_top():
    eski = chat_store.create_conversation("Eski")
    chat_store.create_conversation("Yeni")
    chat_store.add_message(eski, "user", "tekrar gündeme geldi")
    assert chat_store.list_conversations()[0]["id"] == eski


def test_chunks_are_stored_with_the_message():
    cid = chat_store.create_conversation()
    parcalar = [{"source": "git-notlari.md", "text": "## Stash\n\ngit stash", "score": 0.71}]
    chat_store.add_message(cid, "assistant", "git stash kullan", ["git-notlari.md"], parcalar)
    mesaj = chat_store.get_messages(cid)[0]
    assert mesaj["chunks"] == parcalar
    assert chat_store.get_messages(cid)[0]["sources"] == ["git-notlari.md"]


def test_old_databases_get_the_new_column(tmp_path, monkeypatch):
    """chunks_json sonradan eklendi; eski şemalı veritabanı açılabilmeli."""
    import sqlite3

    yol = tmp_path / "eski.db"
    with sqlite3.connect(yol) as c:
        c.execute("CREATE TABLE conversations (id INTEGER PRIMARY KEY AUTOINCREMENT, "
                  "title TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL)")
        c.execute("CREATE TABLE messages (id INTEGER PRIMARY KEY AUTOINCREMENT, "
                  "conversation_id INTEGER NOT NULL, role TEXT NOT NULL, text TEXT NOT NULL, "
                  "sources_json TEXT NOT NULL, created_at TEXT NOT NULL)")
        c.execute("INSERT INTO conversations(title, created_at, updated_at) VALUES ('a','x','x')")
        c.execute("INSERT INTO messages(conversation_id, role, text, sources_json, created_at) "
                  "VALUES (1, 'user', 'eski mesaj', '[]', 'x')")
    monkeypatch.setattr(config, "DB_PATH", yol)
    chat_store.init_db()
    assert chat_store.get_messages(1)[0]["chunks"] == []
