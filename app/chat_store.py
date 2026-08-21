"""Kalıcı sohbet: konuşmalar ve mesajlar aynı SQLite dosyasında tutulur.

Streamlit sürümünde geçmiş yalnızca oturum belleğindeydi; sayfa yenilenince
kayboluyor ve birden fazla sohbet tutulamıyordu. Burada her sohbet bir kayıt,
her mesaj ona bağlı bir satır.
"""
import json
from datetime import datetime

from app.store import connect

DEFAULT_TITLE = "Yeni sohbet"


def _now():
    # Mikrosaniye çözünürlüğü şart: aynı saniye içinde açılan iki sohbetin
    # sıralaması ("en son konuşulan başta") aksi hâlde bozuluyor.
    return datetime.now().isoformat()


def init_db():
    with connect() as c:
        c.execute(
            "CREATE TABLE IF NOT EXISTS conversations ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, "
            "created_at TEXT NOT NULL, updated_at TEXT NOT NULL)"
        )
        c.execute(
            "CREATE TABLE IF NOT EXISTS messages ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, conversation_id INTEGER NOT NULL, "
            "role TEXT NOT NULL, text TEXT NOT NULL, sources_json TEXT NOT NULL, "
            "chunks_json TEXT NOT NULL DEFAULT '[]', created_at TEXT NOT NULL, "
            "FOREIGN KEY(conversation_id) REFERENCES conversations(id) ON DELETE CASCADE)"
        )
        c.execute("CREATE INDEX IF NOT EXISTS idx_messages_conversation "
                  "ON messages(conversation_id)")
        # Şema göçü: kaynak parçaları sonradan eklendi, eski veritabanlarında kolon yok.
        kolonlar = {satir[1] for satir in c.execute("PRAGMA table_info(messages)")}
        if "chunks_json" not in kolonlar:
            c.execute("ALTER TABLE messages ADD COLUMN chunks_json TEXT NOT NULL DEFAULT '[]'")


def create_conversation(title=None):
    zaman = _now()
    with connect() as c:
        cur = c.execute(
            "INSERT INTO conversations(title, created_at, updated_at) VALUES (?, ?, ?)",
            (title or DEFAULT_TITLE, zaman, zaman))
        return cur.lastrowid


def list_conversations():
    """En son konuşulan başta olacak şekilde sohbet listesi."""
    with connect() as c:
        rows = c.execute(
            "SELECT id, title, created_at, updated_at FROM conversations "
            "ORDER BY updated_at DESC, id DESC").fetchall()
    return [{"id": i, "title": t, "created_at": ca, "updated_at": ua} for (i, t, ca, ua) in rows]


def rename_conversation(conversation_id, title):
    with connect() as c:
        c.execute("UPDATE conversations SET title = ?, updated_at = ? WHERE id = ?",
                  (title, _now(), conversation_id))


def delete_conversation(conversation_id):
    with connect() as c:
        c.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
        c.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))


def add_message(conversation_id, role, text, sources=None, chunks=None):
    """Mesajı kaydet. `chunks`: kaynak panelinin geçmişte de dolu gelmesi için parça metinleri."""
    zaman = _now()
    with connect() as c:
        cur = c.execute(
            "INSERT INTO messages(conversation_id, role, text, sources_json, chunks_json, "
            "created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (conversation_id, role, text,
             json.dumps(sources or [], ensure_ascii=False),
             json.dumps(chunks or [], ensure_ascii=False), zaman))
        c.execute("UPDATE conversations SET updated_at = ? WHERE id = ?", (zaman, conversation_id))
        return cur.lastrowid


def get_messages(conversation_id):
    with connect() as c:
        rows = c.execute(
            "SELECT id, role, text, sources_json, chunks_json, created_at FROM messages "
            "WHERE conversation_id = ? ORDER BY id", (conversation_id,)).fetchall()
    return [{"id": i, "role": r, "text": t, "sources": json.loads(s),
             "chunks": json.loads(p), "created_at": ca}
            for (i, r, t, s, p, ca) in rows]


def history(conversation_id):
    """assistant.answer_stream()'in beklediği [(rol, metin)] biçimi."""
    return [(m["role"], m["text"]) for m in get_messages(conversation_id)]


def delete_messages_after(conversation_id, message_id):
    """Yeniden üretme için: verilen mesaj ve sonrasını sil."""
    with connect() as c:
        c.execute("DELETE FROM messages WHERE conversation_id = ? AND id >= ?",
                  (conversation_id, message_id))
