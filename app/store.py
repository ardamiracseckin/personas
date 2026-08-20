import json
import sqlite3

from app import config


def connect():
    """Ortak SQLite bağlantısı (chat_store da bunu kullanır)."""
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(config.DB_PATH)


def init_db():
    with connect() as c:
        c.execute(
            "CREATE TABLE IF NOT EXISTS chunks ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "source TEXT NOT NULL, text TEXT NOT NULL, embedding TEXT NOT NULL)"
        )


def clear():
    with connect() as c:
        c.execute("DELETE FROM chunks")


def delete_by_source(source):
    """Tek bir belgenin parçalarını sil (artımlı yeniden yükleme için)."""
    with connect() as c:
        c.execute("DELETE FROM chunks WHERE source = ?", (source,))


def sources():
    """(kaynak, parça sayısı) listesi — arayüzdeki belgeler bölümü için."""
    with connect() as c:
        return [(s, n) for (s, n) in c.execute(
            "SELECT source, COUNT(*) FROM chunks GROUP BY source ORDER BY source")]


def add_chunk(source, text, embedding):
    with connect() as c:
        c.execute(
            "INSERT INTO chunks(source, text, embedding) VALUES (?, ?, ?)",
            (source, text, json.dumps(embedding)),
        )


def all_chunks():
    with connect() as c:
        rows = c.execute("SELECT source, text, embedding FROM chunks").fetchall()
    return [(s, t, json.loads(e)) for (s, t, e) in rows]


def count():
    with connect() as c:
        return c.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
