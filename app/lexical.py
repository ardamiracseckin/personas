"""Yazım hatalarına dayanıklı sözlüksel eşleşme.

Embedding araması anlamı yakalar ama bozuk yazımda zayıflar: "bölgden" ile
"bölgeden" farklı alt-parçalara ayrıldığı için vektörler uzaklaşır. Bu modül
metni sadeleştirip token bazlı bulanık karşılaştırma yapar; `retriever` sonucu
kosinüs skoruyla harmanlar.

Sadeleştirme yalnızca burada uygulanır — sorgu embedding'e ham hâliyle girer,
çünkü çok dilli embedding modeli Türkçe karakterlerle eğitilmiştir.
"""
import re
from difflib import SequenceMatcher

# Büyük harfler önce ASCII karşılığına çevrilir: "İ".lower() Python'da birleşik
# nokta üretir ("i̇") ve eşleşmeyi bozar.
_TR_MAP = str.maketrans({
    "Ç": "C", "Ğ": "G", "I": "I", "İ": "I", "Ö": "O", "Ş": "S", "Ü": "U",
    "ç": "c", "ğ": "g", "ı": "i", "ö": "o", "ş": "s", "ü": "u",
    "â": "a", "Â": "A", "î": "i", "Î": "I", "û": "u", "Û": "U",
})

_NON_WORD_RE = re.compile(r"[^a-z0-9]+")
MIN_TOKEN_LEN = 3      # "de", "mi" gibi ekler eşleşmeye katkı vermez
MATCH_THRESHOLD = 0.8  # SequenceMatcher oranı; bunun altı "farklı kelime" sayılır


def normalize(text):
    """Türkçe metni karşılaştırmaya uygun sade biçime indir."""
    sade = (text or "").translate(_TR_MAP).lower()
    return _NON_WORD_RE.sub(" ", sade).strip()


def tokens(text):
    return [t for t in normalize(text).split() if len(t) >= MIN_TOKEN_LEN]


def fuzzy_score(query, text):
    """Sorgu kelimelerinin kaçının metinde (yaklaşık) karşılığı var: 0.0–1.0."""
    sorgu = tokens(query)
    if not sorgu:
        return 0.0
    hedef = tokens(text)
    if not hedef:
        return 0.0
    tutan = 0
    for kelime in sorgu:
        for aday in hedef:
            if kelime == aday or SequenceMatcher(None, kelime, aday).ratio() >= MATCH_THRESHOLD:
                tutan += 1
                break
    return tutan / len(sorgu)
