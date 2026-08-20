from pathlib import Path

from app import chunking, config, llm, store

TEXT_SUFFIXES = (".txt", ".md")
SUPPORTED_SUFFIXES = TEXT_SUFFIXES + (".pdf",)


def _read_pdf(path):
    """PDF metnini çıkar. Sayfalar boş satırla ayrılır ki parçalama sınır bulabilsin."""
    from pypdf import PdfReader

    sayfalar = [(sayfa.extract_text() or "").strip() for sayfa in PdfReader(str(path)).pages]
    return "\n\n".join(s for s in sayfalar if s)


def read_document(path):
    """Desteklenen bir belgeyi düz metne çevir."""
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix in TEXT_SUFFIXES:
        return path.read_text(encoding="utf-8", errors="ignore")
    if suffix == ".pdf":
        return _read_pdf(path)
    raise ValueError(f"Desteklenmeyen dosya türü: {suffix or path.name}")


def ingest_file(path, embed_fn=None):
    """Tek bir belgeyi (yeniden) yükle. Aynı adlı eski parçalar silinir.

    Arayüzden sürükle-bırak bunu kullanır; tüm bilgi tabanını yeniden gömmek
    gerekmez.
    """
    path = Path(path)
    embed_fn = embed_fn or llm.embed
    text = read_document(path)
    store.init_db()
    store.delete_by_source(path.name)
    chunks = chunking.chunk_text(text, config.MAX_CHUNK_CHARS)
    if not chunks:
        return 0
    for chunk, vec in zip(chunks, embed_fn(chunks)):
        store.add_chunk(path.name, chunk, vec)
    return len(chunks)


def ingest_folder(folder=None, embed_fn=None):
    """Klasörün tamamını sıfırdan yükle. Returns chunk count."""
    folder = Path(folder) if folder else config.DOCUMENTS_DIR
    embed_fn = embed_fn or llm.embed
    store.init_db()
    store.clear()
    total = 0
    for path in sorted(folder.glob("*")):
        if path.suffix.lower() not in SUPPORTED_SUFFIXES:
            continue
        total += ingest_file(path, embed_fn=embed_fn)
    return total


if __name__ == "__main__":
    n = ingest_folder()
    print(f"{n} parça veritabanına eklendi.")
