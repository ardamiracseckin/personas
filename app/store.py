import json
import sqlite3

from app import config


def _conn():
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(config.DB_PATH)


def init_db():
    with _conn() as c:
        c.execute(
            "CREATE TABLE IF NOT EXISTS chunks ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "source TEXT NOT NULL, text TEXT NOT NULL, embedding TEXT NOT NULL)"
        )


def clear():
    with _conn() as c:
        c.execute("DELETE FROM chunks")


def add_chunk(source, text, embedding):
    with _conn() as c:
        c.execute(
            "INSERT INTO chunks(source, text, embedding) VALUES (?, ?, ?)",
            (source, text, json.dumps(embedding)),
        )


def all_chunks():
    with _conn() as c:
        rows = c.execute("SELECT source, text, embedding FROM chunks").fetchall()
    return [(s, t, json.loads(e)) for (s, t, e) in rows]


def count():
    with _conn() as c:
        return c.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
