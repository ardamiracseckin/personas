"""Cevabın getirilen bağlama dayanıp dayanmadığını ölçer.

Otomatik kalite puanı "doğru bilgi cevapta geçiyor mu" diye bakar; bu modül
"cevaptaki bilgi getirilen parçalardan mı geliyor" sorusunu sorar. İkisi farklı
şeydir: model doğru cevabı kendi ezberinden de verebilir ve o durumda RAG
zinciri aslında çalışmamıştır.

Ölçüt sözlükseldir (model gerektirmez): cevaptaki içerik kelimelerinin kaçı
bağlamda (yaklaşık olarak) geçiyor. Sorudan gelen kelimeler sayılmaz, yoksa
soruyu tekrarlayan cevaplar haksız yere yüksek puan alır.
"""
import re

from app import lexical

# Modelin kendi cümle kurma kelimeleri. Bağlamda geçmemeleri uydurma değildir:
# "`ls -la` komutunu kullanın" cevabında bilgi `ls -la`, gerisi cümle kurma.
# Türkçe çekim ekleri yüzünden tam kelime yerine gövde başlangıcı eşleştirilir
# ("kullanın", "kullanarak", "kullanmanız" hepsi "kullan" ile başlar).
GLUE_PREFIXES = (
    "kullan", "komut", "yap", "yaz", "calistir", "gerek", "ihtiyac", "lutfen",
    "soru", "cevap", "anla", "belirli", "ayrint", "verilen", "baglam", "asagida",
    "yukarida", "ornek", "olarak", "sekilde", "sunlar", "adim", "once", "sonra",
    "mumkun", "istiyor", "edebilir", "olabilir", "bunun", "bunu", "boylece",
)

# Cevabın kendisi "bilmiyorum" ise dayanak aranmaz.
ABSTENTION_MARKERS = ("bilgi yok", "bilgim yok", "bilmiyorum", "bulamadım")


def _is_abstention(answer):
    dusuk = (answer or "").lower()
    return any(im in dusuk for im in ABSTENTION_MARKERS)


def _is_glue(token):
    return any(token.startswith(on) for on in GLUE_PREFIXES)


def _context_tokens(context_texts):
    tokenlar = set()
    for metin in context_texts or []:
        tokenlar |= set(lexical.tokens(metin))
    return tokenlar


def supported(token, context_tokens):
    if token in context_tokens:
        return True
    from difflib import SequenceMatcher

    return any(SequenceMatcher(None, token, aday).ratio() >= lexical.MATCH_THRESHOLD
               for aday in context_tokens)


def content_tokens(answer, question=None):
    """Cevapta bilgi taşıyan kelimeler: soruyu tekrar edenler ve cümle kurma kelimeleri hariç."""
    soru = set(lexical.tokens(question or ""))
    return [t for t in dict.fromkeys(lexical.tokens(answer))
            if t not in soru and not _is_glue(t)]


def unsupported_tokens(answer, context_texts, question=None):
    """Cevapta geçen ama bağlamda karşılığı olmayan içerik kelimeleri."""
    baglam = _context_tokens(context_texts)
    return [t for t in content_tokens(answer, question) if not supported(t, baglam)]


def score(answer, context_texts, question=None):
    """0.0–1.0 arası dayanak oranı. Çekimser cevaplarda None (ölçüm dışı)."""
    if _is_abstention(answer):
        return None
    baglam = _context_tokens(context_texts)
    adaylar = content_tokens(answer, question)
    if not adaylar or not baglam:
        return 0.0
    tutan = sum(1 for t in adaylar if supported(t, baglam))
    return tutan / len(adaylar)


# --- kod sadakati -----------------------------------------------------------
#
# Sözlüksel oran bulanıktır; komut uydurma ise ikili bir hatadır. `ters tırnak`
# içindeki her ifade bağlamda birebir geçmelidir — geçmiyorsa model komutu
# kendisi türetmiştir ve bu, kullanıcının çalıştıracağı yanlış komut demektir.

_CODE_RE = re.compile(r"`([^`\n]+)`")


def _squash(text):
    """Boşlukları at: 'Cmd + Shift + 4' ile 'Cmd+Shift+4' aynı komuttur."""
    return "".join((text or "").lower().split())


def code_spans(text):
    return [m.group(1).strip() for m in _CODE_RE.finditer(text or "") if m.group(1).strip()]


def unsupported_code_spans(answer, context_texts):
    """Cevapta geçen ama bağlamda bulunmayan kod/komut ifadeleri."""
    baglam = _squash("\n".join(context_texts or []))
    return [ifade for ifade in dict.fromkeys(code_spans(answer))
            if _squash(ifade) not in baglam]
