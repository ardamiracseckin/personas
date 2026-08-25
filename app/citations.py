"""Satır içi atıf: cevabın hangi cümlesi hangi getirilen parçadan geliyor.

Model istemine "kaynak numarası yaz" kuralı eklemek çıktı token'ı ve gecikme
demektir; küçük modeller numaraları da karıştırır. Bunun yerine atıf cevap
üretildikten sonra, sadakat ölçümüyle aynı sözlüksel eşleştirmeyle çıkarılır:
gecikme değişmez ve gösterilen atıf, ölçülen dayanakla aynı mantığa dayanır.

Atıflar metnin içine yazılmaz; (start, end) konumları döner. Böylece cevabın
kendisi kirlenmez (kopyala, yeniden üret, ölçüm hep ham metni görür).
"""
import re

from app import grounding, lexical

# Cümlenin bir parçaya bağlanması için o parçadan gelmesi gereken kelime oranı.
# Altında kalan cümle atıfsız bırakılır — yanlış atıf, atıfsızlıktan kötüdür.
CITE_THRESHOLD = 0.55

_FENCE_RE = re.compile(r"```[\s\S]*?```")
_INLINE_CODE_RE = re.compile(r"`[^`\n]+`")
_SENTENCE_END_RE = re.compile(r"[.!?…]+(?=\s|$)")
# Madde imi ve başlık işaretleri cümlenin kendisi değildir.
_LEADING_MARK_RE = re.compile(r"^\s*(?:[-*+]\s+|\d+[.)]\s+|#{1,4}\s+|>\s?)")


def _mask(text):
    """Kod bölgelerini aynı uzunlukta doldurucuyla değiştir: konumlar korunur.

    Amaç `requirements.txt` ya da `a.b` içindeki noktanın cümle sonu sanılmaması.
    Kod bloğu tamamen boşluğa çevrilir; içine atıf konmaz.
    """
    masked = list(text)
    for m in _FENCE_RE.finditer(text):
        for i in range(*m.span()):
            masked[i] = "\n" if text[i] == "\n" else " "
    maskeli = "".join(masked)
    for m in _INLINE_CODE_RE.finditer(maskeli):
        for i in range(*m.span()):
            masked[i] = "x"
    return "".join(masked)


def spans(answer):
    """Cevabın cümlelerini (start, end) olarak ver. Kod blokları atlanır."""
    metin = answer or ""
    maskeli = _mask(metin)
    parcalar = []
    for satir in _line_spans(maskeli):
        parcalar += _sentence_spans(maskeli, *satir)
    return [(b, s) for (b, s) in parcalar if grounding.content_tokens(metin[b:s])]


def _line_spans(maskeli):
    konum, out = 0, []
    for satir in maskeli.split("\n"):
        bas, son = konum, konum + len(satir)
        isaret = _LEADING_MARK_RE.match(satir)
        if isaret:
            bas += isaret.end()
        if satir.strip():
            out.append((bas, son))
        konum = son + 1
    return out


def _sentence_spans(maskeli, bas, son):
    out, konum = [], bas
    for m in _SENTENCE_END_RE.finditer(maskeli, bas, son):
        out.append((konum, m.end()))
        konum = m.end()
    if konum < son:
        out.append((konum, son))
    return [(b + len(maskeli[b:s]) - len(maskeli[b:s].lstrip()), s) for (b, s) in out
            if maskeli[b:s].strip()]


def _support(sentence, chunk_text):
    """Cümledeki içerik kelimelerinin kaçı bu parçada geçiyor: 0.0–1.0."""
    kelimeler = grounding.content_tokens(sentence)
    if not kelimeler:
        return 0.0
    baglam = set(lexical.tokens(chunk_text))
    return sum(1 for k in kelimeler if grounding.supported(k, baglam)) / len(kelimeler)


def attribute(answer, chunks, threshold=CITE_THRESHOLD):
    """Her cümle için en çok örtüşen parça. Eşiği geçmeyen cümle atıfsız kalır."""
    if not chunks:
        return []
    atiflar = []
    for (bas, son) in spans(answer):
        cumle = (answer or "")[bas:son]
        puanlar = [(_support(cumle, c["text"]), i) for i, c in enumerate(chunks)]
        en_iyi, indeks = max(puanlar, key=lambda p: (p[0], -p[1]))
        if en_iyi >= threshold:
            atiflar.append({"start": bas, "end": son, "chunk": indeks,
                            "source": chunks[indeks]["source"], "score": round(en_iyi, 2)})
    return atiflar
