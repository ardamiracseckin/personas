from pathlib import Path

from app import chunking, config, llm, store


def ingest_folder(folder=None, embed_fn=None):
    """Read .txt/.md files, chunk them, embed each chunk, and store. Returns chunk count."""
    folder = Path(folder) if folder else config.DOCUMENTS_DIR
    embed_fn = embed_fn or llm.embed
    store.init_db()
    store.clear()
    total = 0
    for path in sorted(folder.glob("*")):
        if path.suffix.lower() not in (".txt", ".md"):
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        chunks = chunking.chunk_text(text, config.MAX_CHUNK_CHARS)
        if not chunks:
            continue
        vectors = embed_fn(chunks)
        for chunk, vec in zip(chunks, vectors):
            store.add_chunk(path.name, chunk, vec)
            total += 1
    return total


if __name__ == "__main__":
    n = ingest_folder()
    print(f"{n} parça veritabanına eklendi.")
