CAL_WORDS = ("takvim", "etkinlik", "toplantı", "randevu", "bugün ne", "yarın", "ajanda")
MAIL_WORDS = ("mail", "e-posta", "eposta", "gelen kutusu", "okunmamış", "mesaj")
WRITE_WORDS = ("ekle", "oluştur", "kur", "ayarla", "gönder", "yolla", "ilet", "at ")


def route(query):
    """Classify a query into a tool and a read/write action. Defaults to documents/read."""
    q = query.lower()
    is_write = any(w in q for w in WRITE_WORDS)
    if any(w in q for w in CAL_WORDS):
        return {"tool": "calendar", "action": "write" if is_write else "read"}
    if any(w in q for w in MAIL_WORDS):
        return {"tool": "mail", "action": "write" if is_write else "read"}
    return {"tool": "documents", "action": "read"}
