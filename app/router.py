"""Sorguyu bir araca (belge / takvim / mail / uygulama) ve bir niyete eşler.

Araç seçimi ağırlıklı puanlamayla yapılır. Sabit bir sıra kullanmak yanlış sonuç
veriyordu: takvim kelimeleri önce bakıldığı için "toplantı hakkında mail gönder"
takvime gidiyordu. Bazı kelimeler aracı kesin belirler (takvim, gelen kutusu),
bazıları ise zayıf ipuçudur ve başka bir aracın konusu olabilir ("toplantı",
"yarın" bir mailin konusu da olabilir).
"""
import re

CAL_STRONG = ("takvim", "ajanda", "randevu", "etkinlik")
CAL_WEAK = ("toplantı", "yarın", "bugün ne", "ders", "sınav")
MAIL_STRONG = ("mail", "e-posta", "eposta", "gelen kutusu", "okunmamış")
MAIL_WEAK = ("mesaj", "ilet")

STRONG, WEAK = 2, 1
ADDRESS_BONUS = 3  # e-posta adresi geçiyorsa istek neredeyse kesin mail'dir

_ADDRESS_RE = re.compile(r"[\w.\-]+@[\w.\-]+\.\w+")

# Çok harfli fiillerde ek almış biçimler de yakalansın diye alt dize araması
# yeterli ("ekle" → "ekleyebilir misin"). Kısa ve başka kelimelerin içinde
# geçebilen fiiller ayrı ve tam kelime olarak aranır: "sanat" içindeki "at",
# "yazılım" içindeki "yaz" yazma niyeti değildir.
WRITE_WORDS = ("ekle", "oluştur", "kur", "ayarla", "gönder", "yolla")
_WRITE_SHORT_RE = re.compile(r"\b(at|yaz|ilet)\b")

# "aç/başlat/çalıştır" yalnızca tam kelime olarak (\b) eşleşsin ki "açıkla",
# "araç", "ihtiyaç" gibi kelimeleri yanlışlıkla tetiklemesin.
_APP_VERB_RE = re.compile(r"\b(aç|başlat|çalıştır)\b")


def _score(query, strong, weak):
    return (sum(STRONG for w in strong if w in query)
            + sum(WEAK for w in weak if w in query))


def route(query):
    """Classify a query into a tool and action. Defaults to documents/read."""
    q = query.lower()
    is_write = any(w in q for w in WRITE_WORDS) or bool(_WRITE_SHORT_RE.search(q))

    cal = _score(q, CAL_STRONG, CAL_WEAK)
    mail = _score(q, MAIL_STRONG, MAIL_WEAK)
    if _ADDRESS_RE.search(q):
        mail += ADDRESS_BONUS

    if cal or mail:
        tool = "mail" if mail >= cal else "calendar"
        return {"tool": tool, "action": "write" if is_write else "read"}
    if _APP_VERB_RE.search(q):
        return {"tool": "app", "action": "open"}
    return {"tool": "documents", "action": "read"}
