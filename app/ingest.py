from pathlib import Path

from app import chunking, config, llm, mevzuat, store

TEXT_SUFFIXES = (".txt", ".md")
SUPPORTED_SUFFIXES = TEXT_SUFFIXES + (".pdf",)


def _read_pdf(path):
    """PDF metnini çıkar. Sayfalar boş satırla ayrılır ki parçalama sınır bulabilsin.

    `layout` kipi ölçümle seçildi. Varsayılan kip kanun metninde kelimeleri
    bölüyordu ("sözle şmesini", "t arihinden"); sekiz kanunda 533 yerde. Bu hem
    kelime aramasını hem embedding'i bozar ve metni onarmak güvenli değildir:
    kırılma kelimenin başında da olabiliyor sonunda da, sözlük olmadan hangi
    tarafa ekleneceği bilinemez. Layout kipi kırılmaları 59'a indiriyor (%89) ve
    üstelik 20 madde daha buluyor.
    """
    from pypdf import PdfReader

    sayfalar = [(sayfa.extract_text(extraction_mode="layout") or "").strip()
                for sayfa in PdfReader(str(path)).pages]
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


# --- mevzuat: madde bazlı yükleme -------------------------------------------
#
# Kanun metni genel parçalayıcıya verilemez: karakter sınırıyla bölmek maddeyi
# ortasından keser ve atıf anlamını yitirir. Bu yol maddeyi birim alır ve atfı
# parçanın ilk satırına yazar — böylece modele giden bağlamda madde numarası
# hep bulunur ve model onu uydurmak zorunda kalmaz.


def mevzuat_parcalari(text, kaynak, max_chars=None):
    """Kanun metnini (kaynak, text, madde) sözlüklerine çevir."""
    parcalar = []
    for p in mevzuat.parcala(text, max_chars=max_chars or mevzuat.MAX_PARCA):
        parcalar.append({"source": kaynak, "madde": p.madde,
                         "text": f"{p.kunye}\n\n{p.metin}"})
    return parcalar


def ingest_mevzuat_text(text, kaynak, embed_fn=None):
    """Bir kanunun metnini bilgi tabanına yaz. Eski parçaları değiştirir."""
    embed_fn = embed_fn or llm.embed
    store.init_db()
    store.delete_by_source(kaynak)
    parcalar = mevzuat_parcalari(text, kaynak)
    if not parcalar:
        return {"source": kaynak, "chunks": 0}
    vektorler = embed_fn([p["text"] for p in parcalar])
    for p, v in zip(parcalar, vektorler):
        store.add_chunk(p["source"], p["text"], v)
    return {"source": kaynak, "chunks": len(parcalar)}


def ingest_mevzuat_file(path, kaynak=None, embed_fn=None):
    """Kanun PDF'ini oku ve yükle."""
    path = Path(path)
    metin = read_document(path)
    bilgi = mevzuat.kanun_bilgisi(metin)
    ad = kaynak or (f"{bilgi.numara} sayılı {mevzuat.turkce_baslik(bilgi.ad)}" if bilgi.numara
                    else path.stem)
    return ingest_mevzuat_text(metin, kaynak=ad, embed_fn=embed_fn)
